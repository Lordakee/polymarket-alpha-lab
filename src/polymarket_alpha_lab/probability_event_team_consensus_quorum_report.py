"""Read-only team consensus quorum report for probability event research."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from re import Pattern, compile
from typing import Mapping


__all__ = (
    "PROBABILITY_EVENT_TEAM_CONSENSUS_QUORUM_REPORT_VERSION",
    "ProbabilityEventTeamConsensusQuorumInput",
    "ProbabilityEventTeamConsensusQuorumReport",
    "build_probability_event_team_consensus_quorum_report",
    "probability_event_team_consensus_quorum_report_payload",
    "probability_event_team_consensus_quorum_report_digest",
)


PROBABILITY_EVENT_TEAM_CONSENSUS_QUORUM_REPORT_VERSION = (
    "probability-event-team-consensus-quorum-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
CONFIDENCE_FLOOR = Decimal("0.700000")
SEVERITY_CEILING = Decimal("0.700000")
MATERIAL_DISSENT_COUNT = Decimal("2.000000")
DIGEST_RE: Pattern[str] = compile(r"^[0-9a-f]{64}$")

STATUS_CONSENSUS_REACHED = "consensus_reached"
STATUS_QUORUM_BLOCKED = "quorum_blocked"
STATUS_MANUAL_REVIEW_REQUIRED = "manual_review_required"
CONSENSUS_STATUSES = (
    STATUS_CONSENSUS_REACHED,
    STATUS_QUORUM_BLOCKED,
    STATUS_MANUAL_REVIEW_REQUIRED,
)

REASON_REQUIRED_QUORUM_MET = "required_quorum_met"
REASON_REQUIRED_QUORUM_MISSING = "required_quorum_missing"
REASON_CONFIDENCE_READY = "confidence_ready"
REASON_CONFIDENCE_BELOW_FLOOR = "confidence_below_floor"
REASON_DISSENT_PRESENT = "dissent_present"
REASON_DISAGREEMENT_SEVERITY_HIGH = "disagreement_severity_high"
REASON_CODES = (
    REASON_REQUIRED_QUORUM_MET,
    REASON_REQUIRED_QUORUM_MISSING,
    REASON_DISSENT_PRESENT,
    REASON_CONFIDENCE_READY,
    REASON_CONFIDENCE_BELOW_FLOOR,
    REASON_DISAGREEMENT_SEVERITY_HIGH,
)

STEP_PREPARE_SUMMARY = "prepare_readonly_public_probability_summary"
STEP_COLLECT_REVIEWS = "collect_additional_team_reviews_before_public_summary"
STEP_ROUTE_RECONCILIATION = "route_to_manual_probability_reconciliation"
MANUAL_STEPS = (
    STEP_PREPARE_SUMMARY,
    STEP_COLLECT_REVIEWS,
    STEP_ROUTE_RECONCILIATION,
)

PUBLIC_FIELDS = (
    "config_version",
    "supporting_team_count",
    "dissenting_team_count",
    "required_consensus_count",
    "average_confidence_probability",
    "disagreement_severity_probability",
    "consensus_status",
    "reason_codes",
    "manual_next_step",
    "paper_only",
    "report_only",
    "readonly",
    "payload_digest",
)
_SORTED_JSON = {"sort_keys": True}


class ProbabilityEventTeamConsensusQuorumPublicPayload(dict[str, object]):
    """Immutable public payload for the team consensus quorum report."""

    def __readonly(self, *args: object, **kwargs: object) -> None:
        raise TypeError("public_payload is immutable")

    __setitem__ = __readonly
    __delitem__ = __readonly
    clear = __readonly
    pop = __readonly
    popitem = __readonly
    setdefault = __readonly
    update = __readonly


@dataclass(frozen=True)
class ProbabilityEventTeamConsensusQuorumInput:
    supporting_team_count: Decimal
    dissenting_team_count: Decimal
    required_consensus_count: Decimal
    average_confidence_probability: Decimal
    disagreement_severity_probability: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventTeamConsensusQuorumInput:
            raise TypeError(
                "ProbabilityEventTeamConsensusQuorumInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventTeamConsensusQuorumInput:
            raise ValueError(
                "input must be exactly ProbabilityEventTeamConsensusQuorumInput",
            )
        object.__setattr__(
            self,
            "supporting_team_count",
            _require_whole_decimal("supporting_team_count", self.supporting_team_count),
        )
        object.__setattr__(
            self,
            "dissenting_team_count",
            _require_whole_decimal("dissenting_team_count", self.dissenting_team_count),
        )
        object.__setattr__(
            self,
            "required_consensus_count",
            _require_positive_whole_decimal(
                "required_consensus_count",
                self.required_consensus_count,
            ),
        )
        object.__setattr__(
            self,
            "average_confidence_probability",
            _require_probability_decimal(
                "average_confidence_probability",
                self.average_confidence_probability,
            ),
        )
        object.__setattr__(
            self,
            "disagreement_severity_probability",
            _require_probability_decimal(
                "disagreement_severity_probability",
                self.disagreement_severity_probability,
            ),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ProbabilityEventTeamConsensusQuorumReport:
    config_version: str
    supporting_team_count: Decimal
    dissenting_team_count: Decimal
    required_consensus_count: Decimal
    average_confidence_probability: Decimal
    disagreement_severity_probability: Decimal
    consensus_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventTeamConsensusQuorumReport:
            raise TypeError(
                "ProbabilityEventTeamConsensusQuorumReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventTeamConsensusQuorumReport:
            raise ValueError(
                "report must be exactly ProbabilityEventTeamConsensusQuorumReport",
            )
        _require_config_version(self.config_version)
        object.__setattr__(
            self,
            "supporting_team_count",
            _require_whole_decimal("supporting_team_count", self.supporting_team_count),
        )
        object.__setattr__(
            self,
            "dissenting_team_count",
            _require_whole_decimal("dissenting_team_count", self.dissenting_team_count),
        )
        object.__setattr__(
            self,
            "required_consensus_count",
            _require_positive_whole_decimal(
                "required_consensus_count",
                self.required_consensus_count,
            ),
        )
        object.__setattr__(
            self,
            "average_confidence_probability",
            _require_probability_decimal(
                "average_confidence_probability",
                self.average_confidence_probability,
            ),
        )
        object.__setattr__(
            self,
            "disagreement_severity_probability",
            _require_probability_decimal(
                "disagreement_severity_probability",
                self.disagreement_severity_probability,
            ),
        )
        _require_consensus_status(self.consensus_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_manual_next_step(self.manual_next_step)
        _require_digest("payload_digest", self.payload_digest)
        _require_hard_flags(self)
        _validate_report(self)
        expected_digest = _payload_digest(_payload_items(self, payload_digest=""))
        if self.payload_digest != expected_digest:
            raise ValueError("payload_digest must match public payload")

    @property
    def public_payload(self) -> ProbabilityEventTeamConsensusQuorumPublicPayload:
        payload = ProbabilityEventTeamConsensusQuorumPublicPayload(
            _payload_items(self, payload_digest=self.payload_digest),
        )
        _validate_public_payload(payload)
        return payload


def build_probability_event_team_consensus_quorum_report(
    inputs: ProbabilityEventTeamConsensusQuorumInput,
) -> ProbabilityEventTeamConsensusQuorumReport:
    """Build a deterministic paper-only team consensus quorum summary."""

    if type(inputs) is not ProbabilityEventTeamConsensusQuorumInput:
        raise ValueError(
            "inputs must be a ProbabilityEventTeamConsensusQuorumInput",
        )
    _require_hard_flags(inputs)
    status = _consensus_status(inputs)
    values: dict[str, object] = {
        "config_version": PROBABILITY_EVENT_TEAM_CONSENSUS_QUORUM_REPORT_VERSION,
        "supporting_team_count": inputs.supporting_team_count,
        "dissenting_team_count": inputs.dissenting_team_count,
        "required_consensus_count": inputs.required_consensus_count,
        "average_confidence_probability": inputs.average_confidence_probability,
        "disagreement_severity_probability": inputs.disagreement_severity_probability,
        "consensus_status": status,
        "reason_codes": _reason_codes(inputs, status),
        "manual_next_step": _manual_next_step(status),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ProbabilityEventTeamConsensusQuorumReport(
        **values,
        payload_digest=_payload_digest(_payload_values(values, payload_digest="")),
    )


def probability_event_team_consensus_quorum_report_payload(
    report: ProbabilityEventTeamConsensusQuorumReport,
) -> ProbabilityEventTeamConsensusQuorumPublicPayload:
    if type(report) is not ProbabilityEventTeamConsensusQuorumReport:
        raise ValueError("report must be a ProbabilityEventTeamConsensusQuorumReport")
    _require_hard_flags(report)
    _validate_report(report)
    expected_digest = probability_event_team_consensus_quorum_report_digest(report)
    if report.payload_digest != expected_digest:
        raise ValueError("payload_digest must match report payload")
    return report.public_payload


def probability_event_team_consensus_quorum_report_digest(
    report: ProbabilityEventTeamConsensusQuorumReport,
) -> str:
    if type(report) is not ProbabilityEventTeamConsensusQuorumReport:
        raise ValueError("report must be a ProbabilityEventTeamConsensusQuorumReport")
    _require_hard_flags(report)
    _validate_report(report)
    return _payload_digest(_payload_items(report, payload_digest=""))


def _validate_report(report: ProbabilityEventTeamConsensusQuorumReport) -> None:
    expected_status = _consensus_status(report)
    if report.consensus_status != expected_status:
        raise ValueError("consensus_status must match consensus inputs")
    if report.reason_codes != _reason_codes(report, expected_status):
        raise ValueError("reason_codes must match consensus inputs")
    if report.manual_next_step != _manual_next_step(expected_status):
        raise ValueError("manual_next_step must match consensus status")


def _validate_public_payload(
    payload: Mapping[str, object],
) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    if tuple(payload) != PUBLIC_FIELDS:
        raise ValueError("payload must match the canonical quorum schema")
    _require_config_version(payload["config_version"])
    for field_name in (
        "supporting_team_count",
        "dissenting_team_count",
        "required_consensus_count",
    ):
        value = payload[field_name]
        if type(value) is not str:
            raise ValueError(f"{field_name} must be serialized as a string")
        if field_name == "required_consensus_count":
            _require_positive_whole_decimal(field_name, Decimal(value))
        else:
            _require_whole_decimal(field_name, Decimal(value))
    for field_name in (
        "average_confidence_probability",
        "disagreement_severity_probability",
    ):
        value = payload[field_name]
        if type(value) is not str:
            raise ValueError(f"{field_name} must be serialized as a string")
        _require_probability_decimal(field_name, Decimal(value))
    _require_consensus_status(payload["consensus_status"])
    _normalize_reason_codes(payload["reason_codes"])
    _require_manual_next_step(payload["manual_next_step"])
    for flag_name in ("paper_only", "report_only", "readonly"):
        if payload[flag_name] is not True:
            raise ValueError(f"{flag_name} must be True")
    digest = payload["payload_digest"]
    _require_digest("payload_digest", digest)
    unsigned = dict(payload)
    unsigned["payload_digest"] = ""
    if digest != _payload_digest(unsigned):
        raise ValueError("payload_digest must match public payload")
    return payload


def _payload_items(
    report: ProbabilityEventTeamConsensusQuorumReport,
    *,
    payload_digest: str,
) -> dict[str, object]:
    return _payload_values(_report_values_without_digest(report), payload_digest=payload_digest)


def _report_values_without_digest(
    report: ProbabilityEventTeamConsensusQuorumReport,
) -> dict[str, object]:
    return {
        "config_version": report.config_version,
        "supporting_team_count": report.supporting_team_count,
        "dissenting_team_count": report.dissenting_team_count,
        "required_consensus_count": report.required_consensus_count,
        "average_confidence_probability": report.average_confidence_probability,
        "disagreement_severity_probability": report.disagreement_severity_probability,
        "consensus_status": report.consensus_status,
        "reason_codes": report.reason_codes,
        "manual_next_step": report.manual_next_step,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _payload_values(values: Mapping[str, object], *, payload_digest: str) -> dict[str, object]:
    return {
        "config_version": values["config_version"],
        "supporting_team_count": _decimal_text(values["supporting_team_count"]),
        "dissenting_team_count": _decimal_text(values["dissenting_team_count"]),
        "required_consensus_count": _decimal_text(values["required_consensus_count"]),
        "average_confidence_probability": _decimal_text(
            values["average_confidence_probability"],
        ),
        "disagreement_severity_probability": _decimal_text(
            values["disagreement_severity_probability"],
        ),
        "consensus_status": values["consensus_status"],
        "reason_codes": values["reason_codes"],
        "manual_next_step": values["manual_next_step"],
        "paper_only": values["paper_only"],
        "report_only": values["report_only"],
        "readonly": values["readonly"],
        "payload_digest": payload_digest,
    }


def _consensus_status(value: object) -> str:
    supporting_team_count = getattr(value, "supporting_team_count")
    dissenting_team_count = getattr(value, "dissenting_team_count")
    required_consensus_count = getattr(value, "required_consensus_count")
    average_confidence_probability = getattr(value, "average_confidence_probability")
    disagreement_severity_probability = getattr(
        value,
        "disagreement_severity_probability",
    )
    if supporting_team_count < required_consensus_count:
        return STATUS_QUORUM_BLOCKED
    if (
        dissenting_team_count >= MATERIAL_DISSENT_COUNT
        or average_confidence_probability < CONFIDENCE_FLOOR
        or disagreement_severity_probability >= SEVERITY_CEILING
    ):
        return STATUS_MANUAL_REVIEW_REQUIRED
    return STATUS_CONSENSUS_REACHED


def _reason_codes(value: object, status: str) -> tuple[str, ...]:
    if status == STATUS_QUORUM_BLOCKED:
        return (REASON_REQUIRED_QUORUM_MISSING,)
    reasons: list[str] = []
    if status == STATUS_CONSENSUS_REACHED:
        reasons.append(REASON_REQUIRED_QUORUM_MET)
    if getattr(value, "dissenting_team_count") >= MATERIAL_DISSENT_COUNT:
        reasons.append(REASON_DISSENT_PRESENT)
    if getattr(value, "average_confidence_probability") >= CONFIDENCE_FLOOR:
        reasons.append(REASON_CONFIDENCE_READY)
    else:
        reasons.append(REASON_CONFIDENCE_BELOW_FLOOR)
    if getattr(value, "disagreement_severity_probability") >= SEVERITY_CEILING:
        reasons.append(REASON_DISAGREEMENT_SEVERITY_HIGH)
    return tuple(reasons)


def _manual_next_step(status: str) -> str:
    if status == STATUS_CONSENSUS_REACHED:
        return STEP_PREPARE_SUMMARY
    if status == STATUS_QUORUM_BLOCKED:
        return STEP_COLLECT_REVIEWS
    return STEP_ROUTE_RECONCILIATION


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        if type(reason_code) is not str or reason_code not in REASON_CODES:
            raise ValueError("reason_codes must be supported")
    return value


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = getattr(value, field_name)
        if flag is not True:
            raise ValueError(f"{field_name} must be True")


def _require_config_version(value: object) -> None:
    if value != PROBABILITY_EVENT_TEAM_CONSENSUS_QUORUM_REPORT_VERSION:
        raise ValueError("config_version must be the supported report version")


def _require_consensus_status(value: object) -> None:
    if type(value) is not str or value not in CONSENSUS_STATUSES:
        raise ValueError("consensus_status must be supported")


def _require_manual_next_step(value: object) -> None:
    if type(value) is not str or value not in MANUAL_STEPS:
        raise ValueError("manual_next_step must be supported")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_whole_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _decimal_text(value: object) -> str:
    if type(value) is not Decimal:
        raise ValueError("public numeric value must be Decimal")
    return format(value.quantize(QUANTUM, rounding=ROUND_HALF_UP), "f")


def _payload_digest(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        payload,
        **_SORTED_JSON,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()
