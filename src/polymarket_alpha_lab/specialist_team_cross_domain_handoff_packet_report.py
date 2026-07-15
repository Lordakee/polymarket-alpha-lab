"""Read-only Phase 1 specialist team handoff packet report."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from typing import Mapping


__all__ = (
    "SpecialistTeamCrossDomainHandoffPacketInput",
    "SpecialistTeamCrossDomainHandoffPacketReport",
    "build_specialist_team_cross_domain_handoff_packet_report",
    "specialist_team_cross_domain_handoff_packet_report_digest",
    "specialist_team_cross_domain_handoff_packet_report_to_payload",
    "validate_specialist_team_cross_domain_handoff_packet_public_payload",
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
CAPACITY_THRESHOLD = Decimal("0.500000")
MANUAL_REVIEW_DEADLINE_HOURS = Decimal("6.000000")

HANDOFF_STATUSES = ("ready", "attention", "blocked")
READY_REASON_CODE = "specialist_team_cross_domain_handoff_ready"

BLOCKED_REASON_SEQUENCE = (
    "handoff_requires_distinct_team_ids",
    "handoff_reason_count_missing",
    "evidence_digest_missing",
    "deadline_hours_missing",
)
ATTENTION_REASON_SEQUENCE = (
    "recipient_capacity_below_handoff_threshold",
    "handoff_deadline_inside_manual_review_window",
)
REASON_CODE_SEQUENCE = (
    *BLOCKED_REASON_SEQUENCE,
    *ATTENTION_REASON_SEQUENCE,
    READY_REASON_CODE,
)
MANUAL_NEXT_STEPS = (
    "send_public_handoff_packet",
    "confirm_recipient_capacity",
    "confirm_handoff_deadline",
    "confirm_recipient_capacity_and_deadline",
    "prepare_manual_handoff_packet",
)
PAYLOAD_KEYS = (
    "primary_team_id",
    "secondary_team_id",
    "handoff_reason_count",
    "evidence_digest_present",
    "recipient_capacity_score",
    "deadline_hours",
    "handoff_status",
    "reason_codes",
    "manual_next_step",
    "paper_only",
    "report_only",
    "readonly",
)
DECIMAL_FIELDS = (
    "handoff_reason_count",
    "recipient_capacity_score",
    "deadline_hours",
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "service_role",
    "bearer ",
    "postgres://",
    "postgresql://",
)


class _HandoffPacketPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _HandoffPacketPublicDataclass and issubclass(
                base,
                _HandoffPacketPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} does not support subclassing")


@dataclass(frozen=True)
class SpecialistTeamCrossDomainHandoffPacketInput(_HandoffPacketPublicDataclass):
    primary_team_id: str
    secondary_team_id: str
    handoff_reason_count: Decimal
    evidence_digest_present: bool
    recipient_capacity_score: Decimal
    deadline_hours: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            SpecialistTeamCrossDomainHandoffPacketInput,
            "handoff packet input",
        )
        for field_name in ("primary_team_id", "secondary_team_id"):
            object.__setattr__(
                self,
                field_name,
                _normalize_public_id(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "handoff_reason_count",
            _normalize_nonnegative_decimal(
                "handoff_reason_count",
                self.handoff_reason_count,
            ),
        )
        _require_bool("evidence_digest_present", self.evidence_digest_present)
        object.__setattr__(
            self,
            "recipient_capacity_score",
            _normalize_ratio(
                "recipient_capacity_score",
                self.recipient_capacity_score,
            ),
        )
        object.__setattr__(
            self,
            "deadline_hours",
            _normalize_nonnegative_decimal("deadline_hours", self.deadline_hours),
        )
        for field_name in ("paper_only", "report_only", "readonly"):
            _require_bool(field_name, getattr(self, field_name))


@dataclass(frozen=True)
class SpecialistTeamCrossDomainHandoffPacketReport(_HandoffPacketPublicDataclass):
    primary_team_id: str
    secondary_team_id: str
    handoff_reason_count: Decimal
    evidence_digest_present: bool
    recipient_capacity_score: Decimal
    deadline_hours: Decimal
    handoff_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            SpecialistTeamCrossDomainHandoffPacketReport,
            "handoff packet report",
        )
        for field_name in ("primary_team_id", "secondary_team_id"):
            object.__setattr__(
                self,
                field_name,
                _normalize_public_id(field_name, getattr(self, field_name)),
            )
        for field_name in DECIMAL_FIELDS:
            if field_name == "recipient_capacity_score":
                normalized = _normalize_ratio(field_name, getattr(self, field_name))
            else:
                normalized = _normalize_nonnegative_decimal(
                    field_name,
                    getattr(self, field_name),
                )
            object.__setattr__(self, field_name, normalized)
        _require_bool("evidence_digest_present", self.evidence_digest_present)
        object.__setattr__(
            self,
            "handoff_status",
            _normalize_member("handoff_status", self.handoff_status, HANDOFF_STATUSES),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "manual_next_step",
            _normalize_member(
                "manual_next_step",
                self.manual_next_step,
                MANUAL_NEXT_STEPS,
            ),
        )
        for field_name in ("paper_only", "report_only", "readonly"):
            _require_bool(field_name, getattr(self, field_name))
            if getattr(self, field_name) is not True:
                raise ValueError(f"{field_name} must be True")
        _validate_report(self)
        _require_or_set_payload_digest(self)

    @property
    def public_payload(self) -> dict[str, object]:
        return specialist_team_cross_domain_handoff_packet_report_to_payload(self)


def build_specialist_team_cross_domain_handoff_packet_report(
    packet: SpecialistTeamCrossDomainHandoffPacketInput,
) -> SpecialistTeamCrossDomainHandoffPacketReport:
    if type(packet) is not SpecialistTeamCrossDomainHandoffPacketInput:
        raise ValueError(
            "packet must be a SpecialistTeamCrossDomainHandoffPacketInput",
        )
    handoff_status, reason_codes, manual_next_step = _handoff_findings(packet)
    return SpecialistTeamCrossDomainHandoffPacketReport(
        primary_team_id=packet.primary_team_id,
        secondary_team_id=packet.secondary_team_id,
        handoff_reason_count=packet.handoff_reason_count,
        evidence_digest_present=packet.evidence_digest_present,
        recipient_capacity_score=packet.recipient_capacity_score,
        deadline_hours=packet.deadline_hours,
        handoff_status=handoff_status,
        reason_codes=reason_codes,
        manual_next_step=manual_next_step,
        paper_only=packet.paper_only,
        report_only=packet.report_only,
        readonly=packet.readonly,
    )


def specialist_team_cross_domain_handoff_packet_report_to_payload(
    report: SpecialistTeamCrossDomainHandoffPacketReport,
) -> dict[str, object]:
    if type(report) is not SpecialistTeamCrossDomainHandoffPacketReport:
        raise ValueError(
            "report must be a SpecialistTeamCrossDomainHandoffPacketReport",
        )
    _validate_report(report)
    payload: dict[str, object] = {
        "primary_team_id": report.primary_team_id,
        "secondary_team_id": report.secondary_team_id,
        "handoff_reason_count": _decimal_to_string(report.handoff_reason_count),
        "evidence_digest_present": report.evidence_digest_present,
        "recipient_capacity_score": _decimal_to_string(
            report.recipient_capacity_score,
        ),
        "deadline_hours": _decimal_to_string(report.deadline_hours),
        "handoff_status": report.handoff_status,
        "reason_codes": list(report.reason_codes),
        "manual_next_step": report.manual_next_step,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    validate_specialist_team_cross_domain_handoff_packet_public_payload(payload)
    return payload


def specialist_team_cross_domain_handoff_packet_report_digest(
    report: SpecialistTeamCrossDomainHandoffPacketReport,
) -> str:
    payload = specialist_team_cross_domain_handoff_packet_report_to_payload(report)
    return _digest_payload(payload)


def validate_specialist_team_cross_domain_handoff_packet_public_payload(
    payload: Mapping[str, object],
) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    if tuple(payload) != PAYLOAD_KEYS:
        raise ValueError("payload must match the canonical handoff packet schema")
    _reject_unsafe_public_values(payload)
    source = SpecialistTeamCrossDomainHandoffPacketInput(
        primary_team_id=payload["primary_team_id"],  # type: ignore[arg-type]
        secondary_team_id=payload["secondary_team_id"],  # type: ignore[arg-type]
        handoff_reason_count=_decimal_from_payload(
            "handoff_reason_count",
            payload["handoff_reason_count"],
        ),
        evidence_digest_present=payload["evidence_digest_present"],  # type: ignore[arg-type]
        recipient_capacity_score=_decimal_from_payload(
            "recipient_capacity_score",
            payload["recipient_capacity_score"],
        ),
        deadline_hours=_decimal_from_payload("deadline_hours", payload["deadline_hours"]),
    )
    expected_status, expected_reason_codes, expected_next_step = _handoff_findings(
        source,
    )
    if _decimal_to_string(source.recipient_capacity_score) != payload[
        "recipient_capacity_score"
    ]:
        raise ValueError("recipient_capacity_score must be canonical")
    if _decimal_to_string(source.handoff_reason_count) != payload[
        "handoff_reason_count"
    ]:
        raise ValueError("handoff_reason_count must be canonical")
    if _decimal_to_string(source.deadline_hours) != payload["deadline_hours"]:
        raise ValueError("deadline_hours must be canonical")
    if (
        payload["handoff_status"] == "ready"
        and source.recipient_capacity_score < CAPACITY_THRESHOLD
    ):
        raise ValueError("recipient_capacity_score must match handoff_status")
    if (
        payload["handoff_status"] == "ready"
        and source.deadline_hours < MANUAL_REVIEW_DEADLINE_HOURS
    ):
        raise ValueError("deadline_hours must match handoff_status")
    if payload["handoff_status"] != expected_status:
        raise ValueError("handoff_status must match packet fields")
    reason_codes = _normalize_payload_reason_codes(
        "reason_codes",
        payload["reason_codes"],
    )
    if reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match packet fields")
    if payload["manual_next_step"] != expected_next_step:
        raise ValueError("manual_next_step must match packet fields")
    for field_name in ("paper_only", "report_only", "readonly"):
        _require_bool(field_name, payload[field_name])
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    return payload


def _handoff_findings(
    packet: SpecialistTeamCrossDomainHandoffPacketInput,
) -> tuple[str, tuple[str, ...], str]:
    blocked: list[str] = []
    if packet.primary_team_id == packet.secondary_team_id:
        blocked.append("handoff_requires_distinct_team_ids")
    if packet.handoff_reason_count == ZERO:
        blocked.append("handoff_reason_count_missing")
    if packet.evidence_digest_present is not True:
        blocked.append("evidence_digest_missing")
    if packet.deadline_hours == ZERO:
        blocked.append("deadline_hours_missing")

    attention: list[str] = []
    if packet.recipient_capacity_score < CAPACITY_THRESHOLD:
        attention.append("recipient_capacity_below_handoff_threshold")
    if ZERO < packet.deadline_hours < MANUAL_REVIEW_DEADLINE_HOURS:
        attention.append("handoff_deadline_inside_manual_review_window")

    if blocked:
        return (
            "blocked",
            _canonical_reason_codes((*tuple(blocked), *tuple(attention))),
            "prepare_manual_handoff_packet",
        )
    if attention:
        reason_codes = _canonical_reason_codes(tuple(attention))
        return "attention", reason_codes, _attention_next_step(reason_codes)
    return "ready", (READY_REASON_CODE,), "send_public_handoff_packet"


def _attention_next_step(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("recipient_capacity_below_handoff_threshold",):
        return "confirm_recipient_capacity"
    if reason_codes == ("handoff_deadline_inside_manual_review_window",):
        return "confirm_handoff_deadline"
    return "confirm_recipient_capacity_and_deadline"


def _validate_report(report: SpecialistTeamCrossDomainHandoffPacketReport) -> None:
    source = SpecialistTeamCrossDomainHandoffPacketInput(
        primary_team_id=report.primary_team_id,
        secondary_team_id=report.secondary_team_id,
        handoff_reason_count=report.handoff_reason_count,
        evidence_digest_present=report.evidence_digest_present,
        recipient_capacity_score=report.recipient_capacity_score,
        deadline_hours=report.deadline_hours,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    expected_status, expected_reason_codes, expected_next_step = _handoff_findings(
        source,
    )
    if report.handoff_status != expected_status:
        raise ValueError("handoff_status must match packet fields")
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match packet fields")
    if report.manual_next_step != expected_next_step:
        raise ValueError("manual_next_step must match packet fields")


def _require_or_set_payload_digest(
    report: SpecialistTeamCrossDomainHandoffPacketReport,
) -> None:
    expected_digest = _digest_payload(
        specialist_team_cross_domain_handoff_packet_report_to_payload(report),
    )
    if report.payload_digest == "":
        object.__setattr__(report, "payload_digest", expected_digest)
        return
    if report.payload_digest != expected_digest:
        raise ValueError("payload_digest must match public payload")


def _normalize_public_id(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "" or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    _reject_unsafe_public_values(value)
    return value


def _normalize_member(
    field_name: str,
    value: object,
    supported_values: tuple[str, ...],
) -> str:
    if type(value) is not str or value not in supported_values:
        raise ValueError(f"{field_name} must be supported")
    return value


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    return _normalize_reason_code_items(field_name, value)


def _normalize_payload_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is list:
        return _normalize_reason_code_items(field_name, tuple(value))
    if type(value) is tuple:
        return _normalize_reason_code_items(field_name, value)
    raise ValueError(f"{field_name} must be a list")


def _normalize_reason_code_items(
    field_name: str,
    reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    seen: set[str] = set()
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in REASON_CODE_SEQUENCE:
            raise ValueError(f"{field_name} contains unsupported reason code")
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
    canonical = _canonical_reason_codes(reason_codes)
    if reason_codes != canonical:
        raise ValueError(f"{field_name} must use canonical sequence")
    return canonical


def _canonical_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in reason_codes)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _decimal_from_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be serialized as a string")
    return Decimal(value)


def _decimal_to_string(value: Decimal) -> str:
    return format(value, "f")


def _reject_unsafe_public_values(value: object) -> None:
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_unsafe_public_values(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_values(item)
        return
    if type(value) is str:
        normalized = value.lower()
        if any(fragment in normalized for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
            raise ValueError("public payload contains unsafe value")


def _digest_payload(payload: dict[str, object]) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
