"""Read-only operator research packet digest chain integrity report."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields, is_dataclass
from decimal import Decimal, InvalidOperation
from typing import Any


__all__ = (
    "OperatorResearchPacketDigestChainIntegrityReport",
    "build_operator_research_packet_digest_chain_integrity_report",
    "operator_research_packet_digest_chain_integrity_report_payload",
)


PASS_REASON_CODE = "operator_research_packet_digest_chain_integrity_pass"
PACKET_DIGEST_MISSING_REASON_CODE = (
    "operator_research_packet_digest_chain_integrity_packet_digest_missing"
)
SOURCE_DIGEST_ABSENT_REASON_CODE = (
    "operator_research_packet_digest_chain_integrity_source_digest_absent"
)
SOURCE_DIGEST_MISSING_REASON_CODE = (
    "operator_research_packet_digest_chain_integrity_source_digest_missing"
)
OPERATOR_NOTE_DIGEST_MISSING_REASON_CODE = (
    "operator_research_packet_digest_chain_integrity_operator_note_digest_missing"
)
TAMPER_CHECK_FAILED_REASON_CODE = (
    "operator_research_packet_digest_chain_integrity_tamper_check_failed"
)

PASS_NEXT_STEP = "manual_review_digest_chain_complete"
WATCH_NEXT_STEP = "manual_review_attach_missing_digests"
BLOCK_NEXT_STEP = "manual_review_rebuild_digest_chain"

ZERO = Decimal("0")


@dataclass(frozen=True)
class OperatorResearchPacketDigestChainIntegrityReport:
    packet_digest_present: bool
    source_digest_count: Decimal
    missing_source_digest_count: Decimal
    operator_note_digest_present: bool
    tamper_check_passed: bool
    chain_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    public_payload: dict[str, Any]
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not OperatorResearchPacketDigestChainIntegrityReport:
            raise TypeError(
                "OperatorResearchPacketDigestChainIntegrityReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not OperatorResearchPacketDigestChainIntegrityReport:
            raise ValueError(
                "report must be exactly OperatorResearchPacketDigestChainIntegrityReport",
            )
        for field_name in (
            "packet_digest_present",
            "operator_note_digest_present",
            "tamper_check_passed",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "source_digest_count",
            _require_nonnegative_whole_decimal(
                "source_digest_count",
                self.source_digest_count,
            ),
        )
        object.__setattr__(
            self,
            "missing_source_digest_count",
            _require_nonnegative_whole_decimal(
                "missing_source_digest_count",
                self.missing_source_digest_count,
            ),
        )
        object.__setattr__(
            self,
            "chain_status",
            _require_chain_status("chain_status", self.chain_status),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "manual_next_step",
            _require_manual_next_step("manual_next_step", self.manual_next_step),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        expected_payload = _public_payload_without_digest(self)
        expected_digest = _payload_digest(expected_payload)
        expected_public_payload = _json_ready(expected_payload)
        supplied_payload = _json_ready(self.public_payload)
        if type(supplied_payload) is not dict:
            raise ValueError("public_payload must be a JSON object")
        if type(expected_public_payload) is not dict:
            raise ValueError("public_payload must be a JSON object")
        if supplied_payload != {**expected_public_payload, "payload_digest": expected_digest}:
            raise ValueError("public_payload must match report fields")
        object.__setattr__(self, "public_payload", supplied_payload)
        object.__setattr__(
            self,
            "payload_digest",
            _require_digest("payload_digest", self.payload_digest),
        )
        if self.payload_digest != expected_digest:
            raise ValueError("payload_digest must match public_payload")


def build_operator_research_packet_digest_chain_integrity_report(
    *,
    packet_digest_present: bool,
    source_digest_count: Decimal,
    missing_source_digest_count: Decimal,
    operator_note_digest_present: bool,
    tamper_check_passed: bool,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> OperatorResearchPacketDigestChainIntegrityReport:
    _require_bool("packet_digest_present", packet_digest_present)
    source_digest_count = _require_nonnegative_whole_decimal(
        "source_digest_count",
        source_digest_count,
    )
    missing_source_digest_count = _require_nonnegative_whole_decimal(
        "missing_source_digest_count",
        missing_source_digest_count,
    )
    _require_bool("operator_note_digest_present", operator_note_digest_present)
    _require_bool("tamper_check_passed", tamper_check_passed)
    _require_hard_flags(
        "builder",
        _FlagValues(
            paper_only=paper_only,
            report_only=report_only,
            readonly=readonly,
        ),
    )

    reason_codes = _reason_codes(
        packet_digest_present=packet_digest_present,
        source_digest_count=source_digest_count,
        missing_source_digest_count=missing_source_digest_count,
        operator_note_digest_present=operator_note_digest_present,
        tamper_check_passed=tamper_check_passed,
    )
    chain_status = _chain_status(reason_codes)
    manual_next_step = _manual_next_step(chain_status)
    payload_without_digest: dict[str, Any] = {
        "packet_digest_present": packet_digest_present,
        "source_digest_count": source_digest_count,
        "missing_source_digest_count": missing_source_digest_count,
        "operator_note_digest_present": operator_note_digest_present,
        "tamper_check_passed": tamper_check_passed,
        "chain_status": chain_status,
        "reason_codes": reason_codes,
        "manual_next_step": manual_next_step,
        "paper_only": paper_only,
        "report_only": report_only,
        "readonly": readonly,
    }
    digest = _payload_digest(payload_without_digest)
    public_payload = {
        **_json_ready(payload_without_digest),
        "payload_digest": digest,
    }

    return OperatorResearchPacketDigestChainIntegrityReport(
        packet_digest_present=packet_digest_present,
        source_digest_count=source_digest_count,
        missing_source_digest_count=missing_source_digest_count,
        operator_note_digest_present=operator_note_digest_present,
        tamper_check_passed=tamper_check_passed,
        chain_status=chain_status,
        reason_codes=reason_codes,
        manual_next_step=manual_next_step,
        public_payload=public_payload,
        payload_digest=digest,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def operator_research_packet_digest_chain_integrity_report_payload(
    report: OperatorResearchPacketDigestChainIntegrityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is OperatorResearchPacketDigestChainIntegrityReport:
        _require_hard_flags("report", report)
        payload = _json_ready(report.public_payload)
    elif type(report) is dict:
        _reject_public_numerics(report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be an OperatorResearchPacketDigestChainIntegrityReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_public_numerics(payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _validate_public_payload(payload)
    return payload


@dataclass(frozen=True)
class _FlagValues:
    paper_only: object
    report_only: object
    readonly: object


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _reason_codes(
    *,
    packet_digest_present: bool,
    source_digest_count: Decimal,
    missing_source_digest_count: Decimal,
    operator_note_digest_present: bool,
    tamper_check_passed: bool,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if not packet_digest_present:
        reasons.append(PACKET_DIGEST_MISSING_REASON_CODE)
    if missing_source_digest_count > ZERO:
        reasons.append(SOURCE_DIGEST_MISSING_REASON_CODE)
    elif source_digest_count == ZERO:
        reasons.append(SOURCE_DIGEST_ABSENT_REASON_CODE)
    if not operator_note_digest_present:
        reasons.append(OPERATOR_NOTE_DIGEST_MISSING_REASON_CODE)
    if not tamper_check_passed:
        reasons.append(TAMPER_CHECK_FAILED_REASON_CODE)
    if not reasons:
        return (PASS_REASON_CODE,)
    return tuple(reasons)


def _chain_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (PASS_REASON_CODE,):
        return "pass"
    if TAMPER_CHECK_FAILED_REASON_CODE in reason_codes:
        return "block"
    if PACKET_DIGEST_MISSING_REASON_CODE in reason_codes:
        return "block"
    if SOURCE_DIGEST_MISSING_REASON_CODE in reason_codes:
        return "block"
    return "watch"


def _manual_next_step(chain_status: str) -> str:
    if chain_status == "pass":
        return PASS_NEXT_STEP
    if chain_status == "watch":
        return WATCH_NEXT_STEP
    if chain_status == "block":
        return BLOCK_NEXT_STEP
    raise ValueError("chain_status must be pass, watch, or block")


def _public_payload_without_digest(
    report: OperatorResearchPacketDigestChainIntegrityReport,
) -> dict[str, Any]:
    return {
        "packet_digest_present": report.packet_digest_present,
        "source_digest_count": report.source_digest_count,
        "missing_source_digest_count": report.missing_source_digest_count,
        "operator_note_digest_present": report.operator_note_digest_present,
        "tamper_check_passed": report.tamper_check_passed,
        "chain_status": report.chain_status,
        "reason_codes": report.reason_codes,
        "manual_next_step": report.manual_next_step,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _validate_report_consistency(
    report: OperatorResearchPacketDigestChainIntegrityReport,
) -> None:
    expected_reason_codes = _reason_codes(
        packet_digest_present=report.packet_digest_present,
        source_digest_count=report.source_digest_count,
        missing_source_digest_count=report.missing_source_digest_count,
        operator_note_digest_present=report.operator_note_digest_present,
        tamper_check_passed=report.tamper_check_passed,
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match digest chain inputs")
    expected_status = _chain_status(expected_reason_codes)
    if report.chain_status != expected_status:
        raise ValueError("chain_status must match reason_codes")
    if report.manual_next_step != _manual_next_step(expected_status):
        raise ValueError("manual_next_step must match chain_status")


def _validate_public_payload(payload: dict[str, Any]) -> None:
    required_keys = {
        "packet_digest_present",
        "source_digest_count",
        "missing_source_digest_count",
        "operator_note_digest_present",
        "tamper_check_passed",
        "chain_status",
        "reason_codes",
        "manual_next_step",
        "payload_digest",
        "paper_only",
        "report_only",
        "readonly",
    }
    if set(payload) != required_keys:
        raise ValueError("report payload must use the supported public schema")
    _require_bool("packet_digest_present", payload["packet_digest_present"])
    source_digest_count = _require_decimal_string(
        "source_digest_count",
        payload["source_digest_count"],
    )
    missing_source_digest_count = _require_decimal_string(
        "missing_source_digest_count",
        payload["missing_source_digest_count"],
    )
    _require_bool("operator_note_digest_present", payload["operator_note_digest_present"])
    _require_bool("tamper_check_passed", payload["tamper_check_passed"])
    expected_digest = _payload_digest(payload)
    if payload["payload_digest"] != expected_digest:
        raise ValueError("payload_digest must match public payload")
    reason_codes = _normalize_reason_codes("reason_codes", tuple(payload["reason_codes"]))
    chain_status = _require_chain_status("chain_status", payload["chain_status"])
    manual_next_step = _require_manual_next_step(
        "manual_next_step",
        payload["manual_next_step"],
    )
    expected_reason_codes = _reason_codes(
        packet_digest_present=payload["packet_digest_present"],
        source_digest_count=source_digest_count,
        missing_source_digest_count=missing_source_digest_count,
        operator_note_digest_present=payload["operator_note_digest_present"],
        tamper_check_passed=payload["tamper_check_passed"],
    )
    if reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match public payload inputs")
    if chain_status != _chain_status(expected_reason_codes):
        raise ValueError("chain_status must match public payload inputs")
    if manual_next_step != _manual_next_step(chain_status):
        raise ValueError("manual_next_step must match public payload inputs")


def _payload_digest(value: dict[str, Any]) -> str:
    payload = dict(value)
    payload.pop("payload_digest", None)
    json_ready = _json_ready(payload)
    encoded = json.dumps(json_ready, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _json_ready(value: object) -> object:
    if type(value) is Decimal:
        return str(value)
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if type(value) is tuple or type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        converted: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            converted[key] = _json_ready(item)
        return converted
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("value is not JSON serializable")


def _reject_public_numerics(value: object) -> None:
    if type(value) is int or isinstance(value, float):
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if type(value) is dict:
        for item in value.values():
            _reject_public_numerics(item)
        return
    if type(value) is list:
        for item in value:
            _reject_public_numerics(item)


def _normalize_reason_codes(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        normalized.append(_require_reason_code(field_name, value))
    if not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(normalized)


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must contain public reason codes")
    if value.lower() != value or " " in value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    return value


def _require_chain_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in {"pass", "watch", "block"}:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_manual_next_step(field_name: str, value: object) -> str:
    if type(value) is not str or value not in {
        PASS_NEXT_STEP,
        WATCH_NEXT_STEP,
        BLOCK_NEXT_STEP,
    }:
        raise ValueError(f"{field_name} must be a supported manual next step")
    return value


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_decimal_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal-derived string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal-derived string") from exc
    return _require_nonnegative_whole_decimal(field_name, parsed)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")
