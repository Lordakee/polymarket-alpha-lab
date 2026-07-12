from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import re


OPERATOR_FINAL_GO_NO_GO_PACKET_READINESS_REPORT_VERSION = (
    "operator-final-go-no-go-packet-readiness-report-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
GATE_COUNT = Decimal("6.000000")

DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")

GATE_FIELDS = (
    "all_required_gates_passed",
    "manual_attestation_present",
    "latest_packet_digest_present",
    "cost_recheck_passed",
    "source_freshness_passed",
    "memory_policy_passed",
)
REASON_BY_FIELD = {
    "all_required_gates_passed": "required_gates_failed",
    "manual_attestation_present": "manual_attestation_missing",
    "latest_packet_digest_present": "latest_packet_digest_missing",
    "cost_recheck_passed": "cost_recheck_failed",
    "source_freshness_passed": "source_freshness_failed",
    "memory_policy_passed": "memory_policy_failed",
}
READY_REASON = "operator_final_go_no_go_packet_ready"
GO_STATUS = "go"
NO_GO_STATUS = "no_go"
READY_STEP = "human_final_review_required"
MANUAL_ATTESTATION_STEP = "collect_manual_attestation_before_final_review"
BLOCKED_STEP = "resolve_blockers_before_final_review"

PAYLOAD_FIELDS = (
    "config_version",
    "go_no_go_status",
    "reason_codes",
    "manual_next_step",
    "all_required_gates_passed",
    "manual_attestation_present",
    "latest_packet_digest_present",
    "cost_recheck_passed",
    "source_freshness_passed",
    "memory_policy_passed",
    "ready_gate_count",
    "blocked_gate_count",
    "ready_ratio",
    "paper_only",
    "report_only",
    "readonly",
    "payload_digest",
)
DECIMAL_PAYLOAD_FIELDS = ("ready_gate_count", "blocked_gate_count", "ready_ratio")

__all__ = (
    "OPERATOR_FINAL_GO_NO_GO_PACKET_READINESS_REPORT_VERSION",
    "OperatorFinalGoNoGoPacketReadinessInput",
    "OperatorFinalGoNoGoPacketReadinessPayload",
    "OperatorFinalGoNoGoPacketReadinessReport",
    "build_operator_final_go_no_go_packet_readiness_report",
    "operator_final_go_no_go_packet_readiness_report_payload",
)


class OperatorFinalGoNoGoPacketReadinessPayload(dict[str, object]):
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
class OperatorFinalGoNoGoPacketReadinessInput:
    all_required_gates_passed: bool
    manual_attestation_present: bool
    latest_packet_digest_present: bool
    cost_recheck_passed: bool
    source_freshness_passed: bool
    memory_policy_passed: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not OperatorFinalGoNoGoPacketReadinessInput:
            raise TypeError(
                "OperatorFinalGoNoGoPacketReadinessInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not OperatorFinalGoNoGoPacketReadinessInput:
            raise ValueError(
                "input must be exactly OperatorFinalGoNoGoPacketReadinessInput",
            )
        for field_name in GATE_FIELDS:
            _require_bool(field_name, getattr(self, field_name))
        _require_hard_flags(self)


@dataclass(frozen=True)
class OperatorFinalGoNoGoPacketReadinessReport:
    config_version: str
    go_no_go_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    all_required_gates_passed: bool
    manual_attestation_present: bool
    latest_packet_digest_present: bool
    cost_recheck_passed: bool
    source_freshness_passed: bool
    memory_policy_passed: bool
    ready_gate_count: Decimal
    blocked_gate_count: Decimal
    ready_ratio: Decimal
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not OperatorFinalGoNoGoPacketReadinessReport:
            raise TypeError(
                "OperatorFinalGoNoGoPacketReadinessReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not OperatorFinalGoNoGoPacketReadinessReport:
            raise ValueError(
                "report must be exactly OperatorFinalGoNoGoPacketReadinessReport",
            )
        _require_public_label("config_version", self.config_version)
        if self.config_version != OPERATOR_FINAL_GO_NO_GO_PACKET_READINESS_REPORT_VERSION:
            raise ValueError("config_version must be the supported report version")
        _require_status(self.go_no_go_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_next_step(self.manual_next_step)
        for field_name in GATE_FIELDS:
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "ready_gate_count",
            _require_count_decimal("ready_gate_count", self.ready_gate_count),
        )
        object.__setattr__(
            self,
            "blocked_gate_count",
            _require_count_decimal("blocked_gate_count", self.blocked_gate_count),
        )
        object.__setattr__(
            self,
            "ready_ratio",
            _require_ratio_decimal("ready_ratio", self.ready_ratio),
        )
        _require_digest("payload_digest", self.payload_digest)
        _require_hard_flags(self)
        _validate_report(self)
        if self.payload_digest != _payload_digest(_payload_items(self, payload_digest="")):
            raise ValueError("payload_digest must match public payload")

    @property
    def public_payload(self) -> OperatorFinalGoNoGoPacketReadinessPayload:
        payload = OperatorFinalGoNoGoPacketReadinessPayload(
            _payload_items(self, payload_digest=self.payload_digest),
        )
        _validate_public_payload(payload)
        return payload


def build_operator_final_go_no_go_packet_readiness_report(
    inputs: OperatorFinalGoNoGoPacketReadinessInput,
) -> OperatorFinalGoNoGoPacketReadinessReport:
    if type(inputs) is not OperatorFinalGoNoGoPacketReadinessInput:
        raise ValueError("inputs must be an OperatorFinalGoNoGoPacketReadinessInput")
    _require_hard_flags(inputs)
    gate_values = {field_name: getattr(inputs, field_name) for field_name in GATE_FIELDS}
    ready_count = _count(sum(1 for value in gate_values.values() if value is True))
    blocked_count = _count(sum(1 for value in gate_values.values() if value is not True))
    reason_codes = tuple(
        REASON_BY_FIELD[field_name]
        for field_name in GATE_FIELDS
        if gate_values[field_name] is not True
    )
    if not reason_codes:
        reason_codes = (READY_REASON,)
    values: dict[str, object] = {
        "config_version": OPERATOR_FINAL_GO_NO_GO_PACKET_READINESS_REPORT_VERSION,
        "go_no_go_status": GO_STATUS if blocked_count == ZERO else NO_GO_STATUS,
        "reason_codes": reason_codes,
        "manual_next_step": _manual_next_step(reason_codes),
        **gate_values,
        "ready_gate_count": ready_count,
        "blocked_gate_count": blocked_count,
        "ready_ratio": _ratio(ready_count, GATE_COUNT),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return OperatorFinalGoNoGoPacketReadinessReport(
        **values,
        payload_digest=_payload_digest(_payload_values(values, payload_digest="")),
    )


def operator_final_go_no_go_packet_readiness_report_payload(
    report: OperatorFinalGoNoGoPacketReadinessReport | Mapping[str, object],
) -> OperatorFinalGoNoGoPacketReadinessPayload:
    if type(report) is OperatorFinalGoNoGoPacketReadinessReport:
        _require_hard_flags(report)
        _validate_report(report)
        if report.payload_digest != _payload_digest(
            _payload_items(report, payload_digest=""),
        ):
            raise ValueError("payload_digest must match report payload")
        return report.public_payload
    if isinstance(report, Mapping):
        _validate_public_payload(report)
        return OperatorFinalGoNoGoPacketReadinessPayload(report)
    raise ValueError(
        "report must be an OperatorFinalGoNoGoPacketReadinessReport or public payload",
    )


def _manual_next_step(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (READY_REASON,):
        return READY_STEP
    if reason_codes == (REASON_BY_FIELD["manual_attestation_present"],):
        return MANUAL_ATTESTATION_STEP
    return BLOCKED_STEP


def _validate_report(report: OperatorFinalGoNoGoPacketReadinessReport) -> None:
    gate_values = tuple(getattr(report, field_name) for field_name in GATE_FIELDS)
    ready_count = _count(sum(1 for value in gate_values if value is True))
    blocked_count = _count(sum(1 for value in gate_values if value is not True))
    if report.ready_gate_count != ready_count:
        raise ValueError("ready_gate_count must match readiness values")
    if report.blocked_gate_count != blocked_count:
        raise ValueError("blocked_gate_count must match readiness values")
    if report.ready_ratio != _ratio(report.ready_gate_count, GATE_COUNT):
        raise ValueError("ready_ratio must match readiness values")
    expected_reasons = tuple(
        REASON_BY_FIELD[field_name]
        for field_name in GATE_FIELDS
        if getattr(report, field_name) is not True
    )
    if not expected_reasons:
        expected_reasons = (READY_REASON,)
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match readiness values")
    if report.go_no_go_status != (GO_STATUS if blocked_count == ZERO else NO_GO_STATUS):
        raise ValueError("go_no_go_status must match readiness values")
    if report.manual_next_step != _manual_next_step(report.reason_codes):
        raise ValueError("manual_next_step must match reason_codes")


def _payload_items(
    report: OperatorFinalGoNoGoPacketReadinessReport,
    *,
    payload_digest: str,
) -> dict[str, object]:
    return {
        "config_version": report.config_version,
        "go_no_go_status": report.go_no_go_status,
        "reason_codes": list(report.reason_codes),
        "manual_next_step": report.manual_next_step,
        "all_required_gates_passed": report.all_required_gates_passed,
        "manual_attestation_present": report.manual_attestation_present,
        "latest_packet_digest_present": report.latest_packet_digest_present,
        "cost_recheck_passed": report.cost_recheck_passed,
        "source_freshness_passed": report.source_freshness_passed,
        "memory_policy_passed": report.memory_policy_passed,
        "ready_gate_count": _decimal_string(report.ready_gate_count),
        "blocked_gate_count": _decimal_string(report.blocked_gate_count),
        "ready_ratio": _decimal_string(report.ready_ratio),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
        "payload_digest": payload_digest,
    }


def _payload_values(
    values: Mapping[str, object],
    *,
    payload_digest: str,
) -> dict[str, object]:
    return {
        "config_version": values["config_version"],
        "go_no_go_status": values["go_no_go_status"],
        "reason_codes": list(values["reason_codes"]),
        "manual_next_step": values["manual_next_step"],
        "all_required_gates_passed": values["all_required_gates_passed"],
        "manual_attestation_present": values["manual_attestation_present"],
        "latest_packet_digest_present": values["latest_packet_digest_present"],
        "cost_recheck_passed": values["cost_recheck_passed"],
        "source_freshness_passed": values["source_freshness_passed"],
        "memory_policy_passed": values["memory_policy_passed"],
        "ready_gate_count": _decimal_string(values["ready_gate_count"]),
        "blocked_gate_count": _decimal_string(values["blocked_gate_count"]),
        "ready_ratio": _decimal_string(values["ready_ratio"]),
        "paper_only": values["paper_only"],
        "report_only": values["report_only"],
        "readonly": values["readonly"],
        "payload_digest": payload_digest,
    }


def _validate_public_payload(payload: Mapping[str, object]) -> None:
    if not isinstance(payload, Mapping):
        raise ValueError("public payload must be a mapping")
    if tuple(payload) != PAYLOAD_FIELDS:
        raise ValueError("public payload fields must match report contract")
    for field_name in DECIMAL_PAYLOAD_FIELDS:
        if type(payload[field_name]) is not str:
            raise ValueError("public payload numerics must be decimal strings")
        _parse_decimal_string(field_name, payload[field_name])
    for field_name in GATE_FIELDS:
        _require_bool(field_name, payload[field_name])
    _require_status(payload["go_no_go_status"])
    _require_next_step(payload["manual_next_step"])
    _require_hard_flags(payload)
    _require_digest("payload_digest", payload["payload_digest"])
    _normalize_reason_codes(_tuple_from_payload(payload["reason_codes"]))
    payload_without_digest = dict(payload)
    payload_without_digest["payload_digest"] = ""
    if payload["payload_digest"] != _payload_digest(payload_without_digest):
        raise ValueError("payload_digest must match public payload")


def _require_bool(name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{name} must be exactly bool")
    return value


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = value[field_name] if isinstance(value, Mapping) else getattr(value, field_name)
        if flag is not True:
            raise ValueError(f"{field_name} must be True")


def _require_count_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return decimal_value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value).quantize(
        QUANTUM,
        rounding=ROUND_HALF_UP,
    )
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return decimal_value


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return (numerator / denominator).quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _decimal_string(value: object) -> str:
    return str(_require_decimal("payload decimal", value).quantize(QUANTUM))


def _parse_decimal_string(name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{name} must be a decimal string")
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{name} must be a decimal string") from exc
    if not parsed.is_finite():
        raise ValueError(f"{name} must be finite")
    if str(parsed.quantize(QUANTUM)) != value:
        raise ValueError(f"{name} must use six decimal places")
    return parsed


def _require_public_label(name: str, value: object) -> str:
    if type(value) is not str or not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{name} must be a public label")
    return value


def _require_digest(name: str, value: object) -> str:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{name} must be lowercase sha256 hex")
    return value


def _require_status(value: object) -> str:
    if type(value) is not str or value not in {GO_STATUS, NO_GO_STATUS}:
        raise ValueError("go_no_go_status must be go or no_go")
    return value


def _require_next_step(value: object) -> str:
    if type(value) is not str or value not in {
        READY_STEP,
        MANUAL_ATTESTATION_STEP,
        BLOCKED_STEP,
    }:
        raise ValueError("manual_next_step must be a supported public step")
    return value


def _normalize_reason_codes(reason_codes: object) -> tuple[str, ...]:
    allowed_codes = (READY_REASON,) + tuple(REASON_BY_FIELD.values())
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in allowed_codes:
            raise ValueError("reason_codes contains unsupported reason code")
    return reason_codes


def _tuple_from_payload(value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError("reason_codes must be a list in public payload")
    if not all(type(item) is str for item in value):
        raise ValueError("reason_codes must contain strings")
    return tuple(value)


def _payload_digest(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return sha256(encoded).hexdigest()
