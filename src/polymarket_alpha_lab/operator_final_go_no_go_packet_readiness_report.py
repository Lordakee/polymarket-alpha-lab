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
ZERO_DIGEST = "0" * 64

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
    "audit_chain_entry_count",
    "audit_chain_tip_digest",
    "expected_source_packet_digest",
    "expected_public_payload_digest",
    "audit_chain_entries",
    "paper_only",
    "report_only",
    "readonly",
    "payload_digest",
)
DECIMAL_PAYLOAD_FIELDS = (
    "ready_gate_count",
    "blocked_gate_count",
    "ready_ratio",
    "audit_chain_entry_count",
)
AUDIT_CHAIN_ENTRY_FIELDS = (
    "entry_id",
    "previous_entry_digest",
    "decision_log_digest",
    "reviewer_attestation_digest",
    "source_packet_digest",
    "public_payload_digest",
    "entry_digest",
)
AUDIT_CHAIN_ENTRY_DIGEST_FIELDS = (
    "entry_id",
    "previous_entry_digest",
    "decision_log_digest",
    "reviewer_attestation_digest",
    "source_packet_digest",
    "public_payload_digest",
)

__all__ = (
    "OPERATOR_FINAL_GO_NO_GO_PACKET_READINESS_REPORT_VERSION",
    "OperatorFinalGoNoGoPacketReadinessInput",
    "OperatorFinalGoNoGoPacketReadinessPayload",
    "OperatorFinalGoNoGoPacketReadinessReport",
    "build_operator_final_go_no_go_packet_readiness_report",
    "operator_final_go_no_go_packet_readiness_report_payload",
)


class OperatorFinalGoNoGoPacketReadinessPayload(dict[str, object]):
    __slots__ = ("__sealed",)

    def __init__(self, value: Mapping[str, object]) -> None:
        if getattr(
            self,
            "_OperatorFinalGoNoGoPacketReadinessPayload__sealed",
            False,
        ):
            raise TypeError("public_payload is immutable")
        super().__init__(value)
        self.__sealed = True

    def __readonly(self, *args: object, **kwargs: object) -> None:
        raise TypeError("public_payload is immutable")

    __setitem__ = __readonly
    __delitem__ = __readonly
    clear = __readonly
    pop = __readonly
    popitem = __readonly
    setdefault = __readonly
    update = __readonly
    __ior__ = __readonly


@dataclass(frozen=True)
class OperatorFinalGoNoGoPacketReadinessInput:
    all_required_gates_passed: bool
    manual_attestation_present: bool
    latest_packet_digest_present: bool
    cost_recheck_passed: bool
    source_freshness_passed: bool
    memory_policy_passed: bool
    audit_chain_entries: tuple[Mapping[str, object], ...]
    expected_source_packet_digest: str
    expected_public_payload_digest: str
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
        object.__setattr__(
            self,
            "expected_source_packet_digest",
            _require_nonzero_digest(
                "expected_source_packet_digest",
                self.expected_source_packet_digest,
                "source packet hash",
            ),
        )
        object.__setattr__(
            self,
            "expected_public_payload_digest",
            _require_nonzero_digest(
                "expected_public_payload_digest",
                self.expected_public_payload_digest,
                "public payload hash",
            ),
        )
        object.__setattr__(
            self,
            "audit_chain_entries",
            _normalize_audit_chain_entries(
                self.audit_chain_entries,
                expected_source_packet_digest=self.expected_source_packet_digest,
                expected_public_payload_digest=self.expected_public_payload_digest,
            ),
        )
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
    audit_chain_entry_count: Decimal
    audit_chain_tip_digest: str
    expected_source_packet_digest: str
    expected_public_payload_digest: str
    audit_chain_entries: tuple[Mapping[str, object], ...]
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
        object.__setattr__(
            self,
            "audit_chain_entry_count",
            _require_count_decimal(
                "audit_chain_entry_count",
                self.audit_chain_entry_count,
            ),
        )
        object.__setattr__(
            self,
            "expected_source_packet_digest",
            _require_nonzero_digest(
                "expected_source_packet_digest",
                self.expected_source_packet_digest,
                "source packet hash",
            ),
        )
        object.__setattr__(
            self,
            "expected_public_payload_digest",
            _require_nonzero_digest(
                "expected_public_payload_digest",
                self.expected_public_payload_digest,
                "public payload hash",
            ),
        )
        object.__setattr__(
            self,
            "audit_chain_entries",
            _normalize_audit_chain_entries(
                self.audit_chain_entries,
                expected_source_packet_digest=self.expected_source_packet_digest,
                expected_public_payload_digest=self.expected_public_payload_digest,
            ),
        )
        _require_digest("audit_chain_tip_digest", self.audit_chain_tip_digest)
        _require_digest("payload_digest", self.payload_digest)
        _require_hard_flags(self)
        _validate_report(self)
        if self.payload_digest != _payload_digest(_payload_items(self, payload_digest="")):
            raise ValueError("payload_digest must match public payload")

    @property
    def public_payload(self) -> OperatorFinalGoNoGoPacketReadinessPayload:
        return _readonly_payload(_materialize_report_payload(self))


def build_operator_final_go_no_go_packet_readiness_report(
    inputs: OperatorFinalGoNoGoPacketReadinessInput,
) -> OperatorFinalGoNoGoPacketReadinessReport:
    if type(inputs) is not OperatorFinalGoNoGoPacketReadinessInput:
        raise ValueError("inputs must be an OperatorFinalGoNoGoPacketReadinessInput")
    _validate_input_object(inputs)
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
        "audit_chain_entry_count": _count(len(inputs.audit_chain_entries)),
        "audit_chain_tip_digest": inputs.audit_chain_entries[-1]["entry_digest"],
        "expected_source_packet_digest": inputs.expected_source_packet_digest,
        "expected_public_payload_digest": inputs.expected_public_payload_digest,
        "audit_chain_entries": inputs.audit_chain_entries,
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
        return _readonly_payload(_materialize_report_payload(report))
    if isinstance(report, Mapping):
        _validate_public_payload(report)
        return _readonly_payload(report)
    raise ValueError(
        "report must be an OperatorFinalGoNoGoPacketReadinessReport or public payload",
    )


def _manual_next_step(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (READY_REASON,):
        return READY_STEP
    if reason_codes == (REASON_BY_FIELD["manual_attestation_present"],):
        return MANUAL_ATTESTATION_STEP
    return BLOCKED_STEP


def _validate_input_object(
    inputs: OperatorFinalGoNoGoPacketReadinessInput,
) -> None:
    if type(inputs) is not OperatorFinalGoNoGoPacketReadinessInput:
        raise ValueError(
            "inputs must be exactly OperatorFinalGoNoGoPacketReadinessInput",
        )
    for field_name in GATE_FIELDS:
        _require_bool(field_name, getattr(inputs, field_name))
    expected_source_packet_digest = _require_nonzero_digest(
        "expected_source_packet_digest",
        inputs.expected_source_packet_digest,
        "source packet hash",
    )
    expected_public_payload_digest = _require_nonzero_digest(
        "expected_public_payload_digest",
        inputs.expected_public_payload_digest,
        "public payload hash",
    )
    _validate_stored_audit_chain_entries(
        inputs.audit_chain_entries,
        expected_source_packet_digest=expected_source_packet_digest,
        expected_public_payload_digest=expected_public_payload_digest,
    )
    _require_hard_flags(inputs)


def _validate_report_object(
    report: OperatorFinalGoNoGoPacketReadinessReport,
) -> None:
    if type(report) is not OperatorFinalGoNoGoPacketReadinessReport:
        raise ValueError(
            "report must be exactly OperatorFinalGoNoGoPacketReadinessReport",
        )
    if type(report.config_version) is not str:
        raise ValueError("config_version must be exactly str")
    _require_public_label("config_version", report.config_version)
    if report.config_version != OPERATOR_FINAL_GO_NO_GO_PACKET_READINESS_REPORT_VERSION:
        raise ValueError("config_version must be the supported report version")
    _require_status(report.go_no_go_status)
    _normalize_reason_codes(report.reason_codes)
    _require_next_step(report.manual_next_step)
    for field_name in GATE_FIELDS:
        _require_bool(field_name, getattr(report, field_name))
    _require_canonical_count_decimal("ready_gate_count", report.ready_gate_count)
    _require_canonical_count_decimal("blocked_gate_count", report.blocked_gate_count)
    _require_canonical_ratio_decimal("ready_ratio", report.ready_ratio)
    _require_canonical_count_decimal(
        "audit_chain_entry_count",
        report.audit_chain_entry_count,
    )
    expected_source_packet_digest = _require_nonzero_digest(
        "expected_source_packet_digest",
        report.expected_source_packet_digest,
        "source packet hash",
    )
    expected_public_payload_digest = _require_nonzero_digest(
        "expected_public_payload_digest",
        report.expected_public_payload_digest,
        "public payload hash",
    )
    _validate_stored_audit_chain_entries(
        report.audit_chain_entries,
        expected_source_packet_digest=expected_source_packet_digest,
        expected_public_payload_digest=expected_public_payload_digest,
    )
    _require_digest("audit_chain_tip_digest", report.audit_chain_tip_digest)
    _require_digest("payload_digest", report.payload_digest)
    _require_hard_flags(report)
    _validate_report(report)
    if report.payload_digest != _payload_digest(
        _payload_items(report, payload_digest=""),
    ):
        raise ValueError("payload_digest must match report payload")


def _materialize_report_payload(
    report: OperatorFinalGoNoGoPacketReadinessReport,
) -> dict[str, object]:
    _validate_report_object(report)
    payload = _payload_items(report, payload_digest=report.payload_digest)
    _validate_public_payload(payload)
    return payload


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
    expected_audit_count = _count(len(report.audit_chain_entries))
    if report.audit_chain_entry_count != expected_audit_count:
        raise ValueError("audit_chain_entry_count must match audit chain")
    if report.audit_chain_tip_digest != report.audit_chain_entries[-1]["entry_digest"]:
        raise ValueError("audit_chain_tip_digest must match digest chain")
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
        "audit_chain_entry_count": _decimal_string(report.audit_chain_entry_count),
        "audit_chain_tip_digest": report.audit_chain_tip_digest,
        "expected_source_packet_digest": report.expected_source_packet_digest,
        "expected_public_payload_digest": report.expected_public_payload_digest,
        "audit_chain_entries": _audit_chain_payload_items(report.audit_chain_entries),
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
        "audit_chain_entry_count": _decimal_string(values["audit_chain_entry_count"]),
        "audit_chain_tip_digest": values["audit_chain_tip_digest"],
        "expected_source_packet_digest": values["expected_source_packet_digest"],
        "expected_public_payload_digest": values["expected_public_payload_digest"],
        "audit_chain_entries": _audit_chain_payload_items(values["audit_chain_entries"]),
        "paper_only": values["paper_only"],
        "report_only": values["report_only"],
        "readonly": values["readonly"],
        "payload_digest": payload_digest,
    }


def _validate_public_payload(payload: Mapping[str, object]) -> None:
    if type(payload) not in {dict, OperatorFinalGoNoGoPacketReadinessPayload}:
        raise ValueError("public payload must be an exact public mapping")
    if tuple(payload) != PAYLOAD_FIELDS:
        raise ValueError("public payload fields must match report contract")
    if type(payload["config_version"]) is not str:
        raise ValueError("config_version must be exactly str")
    _require_public_label("config_version", payload["config_version"])
    if payload["config_version"] != OPERATOR_FINAL_GO_NO_GO_PACKET_READINESS_REPORT_VERSION:
        raise ValueError("config_version must be the supported report version")
    parsed_decimals: dict[str, Decimal] = {}
    for field_name in DECIMAL_PAYLOAD_FIELDS:
        if type(payload[field_name]) is not str:
            raise ValueError("public payload numerics must be decimal strings")
        parsed_decimals[field_name] = _parse_decimal_string(
            field_name,
            payload[field_name],
        )
    for field_name in GATE_FIELDS:
        _require_bool(field_name, payload[field_name])
    _require_status(payload["go_no_go_status"])
    _require_next_step(payload["manual_next_step"])
    reason_codes = _normalize_reason_codes(
        _tuple_from_payload(payload["reason_codes"]),
    )
    expected_source_packet_digest = _require_nonzero_digest(
        "expected_source_packet_digest",
        payload["expected_source_packet_digest"],
        "source packet hash",
    )
    expected_public_payload_digest = _require_nonzero_digest(
        "expected_public_payload_digest",
        payload["expected_public_payload_digest"],
        "public payload hash",
    )
    _validate_public_audit_chain_container(payload["audit_chain_entries"])
    audit_chain_entries = _normalize_audit_chain_entries(
        payload["audit_chain_entries"],
        expected_source_packet_digest=expected_source_packet_digest,
        expected_public_payload_digest=expected_public_payload_digest,
    )
    audit_chain_entry_count = parsed_decimals["audit_chain_entry_count"]
    if audit_chain_entry_count != _count(len(audit_chain_entries)):
        raise ValueError("audit_chain_entry_count must match audit chain")
    _require_digest("audit_chain_tip_digest", payload["audit_chain_tip_digest"])
    if payload["audit_chain_tip_digest"] != audit_chain_entries[-1]["entry_digest"]:
        raise ValueError("audit_chain_tip_digest must match digest chain")
    _require_hard_flags(payload)
    _require_digest("payload_digest", payload["payload_digest"])
    payload_without_digest = dict(payload)
    payload_without_digest["payload_digest"] = ""
    if payload["payload_digest"] != _payload_digest(payload_without_digest):
        raise ValueError("payload_digest must match public payload")

    gate_values = tuple(payload[field_name] for field_name in GATE_FIELDS)
    ready_count = _count(sum(1 for value in gate_values if value is True))
    blocked_count = _count(sum(1 for value in gate_values if value is not True))
    if parsed_decimals["ready_gate_count"] != ready_count:
        raise ValueError("ready_gate_count must match readiness values")
    if parsed_decimals["blocked_gate_count"] != blocked_count:
        raise ValueError("blocked_gate_count must match readiness values")
    if parsed_decimals["ready_ratio"] != _ratio(ready_count, GATE_COUNT):
        raise ValueError("ready_ratio must match readiness values")
    expected_reasons = tuple(
        REASON_BY_FIELD[field_name]
        for field_name in GATE_FIELDS
        if payload[field_name] is not True
    )
    if not expected_reasons:
        expected_reasons = (READY_REASON,)
    if reason_codes != expected_reasons:
        raise ValueError("reason_codes must match readiness values")
    expected_status = GO_STATUS if blocked_count == ZERO else NO_GO_STATUS
    if payload["go_no_go_status"] != expected_status:
        raise ValueError("go_no_go_status must match readiness values")
    if payload["manual_next_step"] != _manual_next_step(reason_codes):
        raise ValueError("manual_next_step must match reason_codes")


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


def _require_canonical_count_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value.as_tuple().exponent != QUANTUM.as_tuple().exponent:
        raise ValueError(f"{name} must use six decimal places")
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return decimal_value


def _require_canonical_ratio_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value.as_tuple().exponent != QUANTUM.as_tuple().exponent:
        raise ValueError(f"{name} must use six decimal places")
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
    decimal_value = _require_decimal("payload decimal", value)
    if decimal_value.as_tuple().exponent != QUANTUM.as_tuple().exponent:
        raise ValueError("payload decimal must use six decimal places")
    return str(decimal_value)


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


def _require_nonzero_digest(name: str, value: object, label: str) -> str:
    digest = _require_digest(name, value)
    if digest == ZERO_DIGEST:
        raise ValueError(f"{label} must be present")
    return digest


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
    if type(value) not in {list, tuple}:
        raise ValueError("reason_codes must be a list in public payload")
    if not all(type(item) is str for item in value):
        raise ValueError("reason_codes must contain strings")
    return tuple(value)


def _normalize_audit_chain_entries(
    entries: object,
    *,
    expected_source_packet_digest: str,
    expected_public_payload_digest: str,
) -> tuple[dict[str, str], ...]:
    if type(entries) not in {list, tuple}:
        raise ValueError("audit_chain_entries must be a sequence")
    if not entries:
        raise ValueError("audit_chain_entries must contain at least one decision")

    normalized_entries: list[dict[str, str]] = []
    expected_previous_entry_digest = ZERO_DIGEST
    for index, entry in enumerate(entries):
        if not isinstance(entry, Mapping):
            raise ValueError("audit_chain_entries must contain mappings")
        if set(entry) != set(AUDIT_CHAIN_ENTRY_FIELDS):
            raise ValueError("audit_chain_entries fields must match contract")

        normalized = {
            "entry_id": _require_public_label("entry_id", entry["entry_id"]),
            "previous_entry_digest": _require_digest(
                "previous_entry_digest",
                entry["previous_entry_digest"],
            ),
            "decision_log_digest": _require_nonzero_digest(
                "decision_log_digest",
                entry["decision_log_digest"],
                "decision log digest",
            ),
            "reviewer_attestation_digest": _require_nonzero_digest(
                "reviewer_attestation_digest",
                entry["reviewer_attestation_digest"],
                "reviewer attestation",
            ),
            "source_packet_digest": _require_nonzero_digest(
                "source_packet_digest",
                entry["source_packet_digest"],
                "source packet hash",
            ),
            "public_payload_digest": _require_nonzero_digest(
                "public_payload_digest",
                entry["public_payload_digest"],
                "public payload hash",
            ),
            "entry_digest": _require_digest("entry_digest", entry["entry_digest"]),
        }
        if normalized["previous_entry_digest"] != expected_previous_entry_digest:
            raise ValueError("digest chain must link consecutive entries")
        if normalized["source_packet_digest"] != expected_source_packet_digest:
            raise ValueError("source packet hash must match audit chain")
        if normalized["public_payload_digest"] != expected_public_payload_digest:
            raise ValueError("public payload hash must match audit chain")
        if normalized["entry_digest"] != _audit_chain_entry_digest(normalized):
            raise ValueError("digest chain entry_digest must match entry payload")
        if index > 0 and normalized["entry_id"] <= normalized_entries[-1]["entry_id"]:
            raise ValueError("digest chain entry_id must be increasing")
        normalized_entries.append(normalized)
        expected_previous_entry_digest = normalized["entry_digest"]
    return tuple(normalized_entries)


def _validate_stored_audit_chain_entries(
    entries: object,
    *,
    expected_source_packet_digest: str,
    expected_public_payload_digest: str,
) -> tuple[dict[str, str], ...]:
    if type(entries) is not tuple:
        raise ValueError("audit_chain_entries must be exactly tuple")
    for entry in entries:
        if type(entry) is not dict:
            raise ValueError("audit_chain_entries must contain exact dict values")
        if tuple(entry) != AUDIT_CHAIN_ENTRY_FIELDS:
            raise ValueError("audit_chain_entries fields must match contract")
    return _normalize_audit_chain_entries(
        entries,
        expected_source_packet_digest=expected_source_packet_digest,
        expected_public_payload_digest=expected_public_payload_digest,
    )


def _validate_public_audit_chain_container(entries: object) -> None:
    if type(entries) not in {list, tuple}:
        raise ValueError("audit_chain_entries must be a public array")
    for entry in entries:
        if type(entry) not in {dict, OperatorFinalGoNoGoPacketReadinessPayload}:
            raise ValueError("audit_chain_entries must contain exact public mappings")
        if tuple(entry) != AUDIT_CHAIN_ENTRY_FIELDS:
            raise ValueError("audit_chain_entries fields must match contract")


def _audit_chain_entry_digest(entry: Mapping[str, object]) -> str:
    digest_payload = {
        field_name: entry[field_name]
        for field_name in AUDIT_CHAIN_ENTRY_DIGEST_FIELDS
    }
    encoded = json.dumps(
        digest_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _audit_chain_payload_items(entries: object) -> tuple[dict[str, str], ...]:
    if type(entries) is not tuple:
        raise ValueError("audit_chain_entries must be exactly tuple")
    return tuple(
        {
            field_name: entry[field_name]
            for field_name in AUDIT_CHAIN_ENTRY_FIELDS
        }
        for entry in entries
    )


def _readonly_payload(
    payload: Mapping[str, object],
) -> OperatorFinalGoNoGoPacketReadinessPayload:
    return OperatorFinalGoNoGoPacketReadinessPayload(
        {
            field_name: _readonly_payload_value(value)
            for field_name, value in payload.items()
        },
    )


def _readonly_payload_value(value: object) -> object:
    if isinstance(value, Mapping):
        return OperatorFinalGoNoGoPacketReadinessPayload(
            {
                field_name: _readonly_payload_value(item)
                for field_name, item in value.items()
            },
        )
    if isinstance(value, (list, tuple)):
        return tuple(_readonly_payload_value(item) for item in value)
    return value


def _payload_digest(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return sha256(encoded).hexdigest()
