"""Read-only source evidence capture chain gap report."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from hashlib import sha256
import json
from typing import Mapping

from polymarket_alpha_lab.team_paper_guard import json_ready_no_floats


__all__ = (
    "CAPTURE_CHAIN_STATUSES",
    "SourceEvidenceCaptureChainGapInput",
    "SourceEvidenceCaptureChainGapReport",
    "build_source_evidence_capture_chain_gap_report",
    "source_evidence_capture_chain_gap_report_digest",
    "source_evidence_capture_chain_gap_report_to_payload",
    "validate_source_evidence_capture_chain_gap_public_payload",
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")

CAPTURE_CHAIN_STATUSES = ("complete", "incomplete", "blocked")
READY_REASON_CODE = "source_evidence_capture_chain_complete"
REASON_CODE_SEQUENCE = (
    "source_evidence_official_anchor_missing",
    "source_evidence_captured_count_below_expected",
    "source_evidence_digest_gap_detected",
    "source_evidence_timestamp_gap_detected",
    READY_REASON_CODE,
)
MANUAL_NEXT_STEPS = (
    "continue_manual_review_with_captured_evidence",
    "manually_reconcile_missing_source_evidence",
    "manually_capture_official_source_anchor",
)
PAYLOAD_FIELDS = (
    "expected_source_count",
    "captured_source_count",
    "digest_gap_count",
    "timestamp_gap_count",
    "official_anchor_present",
    "capture_chain_status",
    "reason_codes",
    "manual_next_step",
    "paper_only",
    "report_only",
    "readonly",
)
COUNT_FIELDS = (
    "expected_source_count",
    "captured_source_count",
    "digest_gap_count",
    "timestamp_gap_count",
)
PRIVATE_VALUE_FRAGMENTS = (
    "postgres://",
    "postgresql://",
    "service_role",
    "bearer ",
)


class _SourceEvidenceCaptureChainPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if (
                base is not _SourceEvidenceCaptureChainPublicDataclass
                and issubclass(base, _SourceEvidenceCaptureChainPublicDataclass)
            ):
                raise TypeError(f"{base.__name__} does not support subclassing")


@dataclass(frozen=True)
class SourceEvidenceCaptureChainGapInput(
    _SourceEvidenceCaptureChainPublicDataclass,
):
    expected_source_count: Decimal
    captured_source_count: Decimal
    digest_gap_count: Decimal
    timestamp_gap_count: Decimal
    official_anchor_present: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            SourceEvidenceCaptureChainGapInput,
            "source evidence capture chain input",
        )
        for field_name in COUNT_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "official_anchor_present",
            "paper_only",
            "report_only",
            "readonly",
        ):
            _require_bool(field_name, getattr(self, field_name))
        if self.captured_source_count > self.expected_source_count:
            raise ValueError("captured_source_count must not exceed expected_source_count")


@dataclass(frozen=True)
class SourceEvidenceCaptureChainGapReport(
    _SourceEvidenceCaptureChainPublicDataclass,
):
    expected_source_count: Decimal
    captured_source_count: Decimal
    digest_gap_count: Decimal
    timestamp_gap_count: Decimal
    official_anchor_present: bool
    capture_chain_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            SourceEvidenceCaptureChainGapReport,
            "source evidence capture chain report",
        )
        for field_name in COUNT_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "official_anchor_present",
            "paper_only",
            "report_only",
            "readonly",
        ):
            _require_bool(field_name, getattr(self, field_name))
        if self.captured_source_count > self.expected_source_count:
            raise ValueError("captured_source_count must not exceed expected_source_count")
        object.__setattr__(
            self,
            "capture_chain_status",
            _normalize_status(self.capture_chain_status),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "manual_next_step",
            _normalize_manual_next_step(self.manual_next_step),
        )
        _validate_report(self)

    @property
    def public_payload(self) -> dict[str, object]:
        return source_evidence_capture_chain_gap_report_to_payload(self)

    @property
    def payload_digest(self) -> str:
        return source_evidence_capture_chain_gap_report_digest(self)


def build_source_evidence_capture_chain_gap_report(
    capture: SourceEvidenceCaptureChainGapInput,
) -> SourceEvidenceCaptureChainGapReport:
    if type(capture) is not SourceEvidenceCaptureChainGapInput:
        raise ValueError("capture must be a SourceEvidenceCaptureChainGapInput")
    status, reason_codes, manual_next_step = _findings(capture)
    return SourceEvidenceCaptureChainGapReport(
        expected_source_count=capture.expected_source_count,
        captured_source_count=capture.captured_source_count,
        digest_gap_count=capture.digest_gap_count,
        timestamp_gap_count=capture.timestamp_gap_count,
        official_anchor_present=capture.official_anchor_present,
        capture_chain_status=status,
        reason_codes=reason_codes,
        manual_next_step=manual_next_step,
        paper_only=capture.paper_only,
        report_only=capture.report_only,
        readonly=capture.readonly,
    )


def source_evidence_capture_chain_gap_report_to_payload(
    report: SourceEvidenceCaptureChainGapReport,
) -> dict[str, object]:
    if type(report) is not SourceEvidenceCaptureChainGapReport:
        raise ValueError("report must be a SourceEvidenceCaptureChainGapReport")
    _validate_report(report)
    payload = json_ready_no_floats(
        {
            "expected_source_count": report.expected_source_count,
            "captured_source_count": report.captured_source_count,
            "digest_gap_count": report.digest_gap_count,
            "timestamp_gap_count": report.timestamp_gap_count,
            "official_anchor_present": report.official_anchor_present,
            "capture_chain_status": report.capture_chain_status,
            "reason_codes": report.reason_codes,
            "manual_next_step": report.manual_next_step,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    validate_source_evidence_capture_chain_gap_public_payload(payload)
    return payload


def source_evidence_capture_chain_gap_report_digest(
    report: SourceEvidenceCaptureChainGapReport,
) -> str:
    return _digest_payload(source_evidence_capture_chain_gap_report_to_payload(report))


def validate_source_evidence_capture_chain_gap_public_payload(
    payload: Mapping[str, object],
) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    if tuple(payload) != PAYLOAD_FIELDS:
        raise ValueError("payload must match the source evidence capture chain schema")
    _reject_private_public_values(payload)

    counts = {
        field_name: _payload_count(field_name, payload[field_name])
        for field_name in COUNT_FIELDS
    }
    official_anchor_present = payload["official_anchor_present"]
    _require_bool("official_anchor_present", official_anchor_present)
    for field_name in ("paper_only", "report_only", "readonly"):
        _require_bool(field_name, payload[field_name])
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")

    source = SourceEvidenceCaptureChainGapInput(
        expected_source_count=counts["expected_source_count"],
        captured_source_count=counts["captured_source_count"],
        digest_gap_count=counts["digest_gap_count"],
        timestamp_gap_count=counts["timestamp_gap_count"],
        official_anchor_present=official_anchor_present,
    )
    expected = build_source_evidence_capture_chain_gap_report(source)

    reason_codes = _normalize_payload_reason_codes(payload["reason_codes"])
    if reason_codes != expected.reason_codes:
        _raise_reason_mismatch(expected.reason_codes)
    capture_chain_status = _normalize_status(payload["capture_chain_status"])
    if capture_chain_status != expected.capture_chain_status:
        raise ValueError("capture_chain_status must match source evidence fields")
    manual_next_step = _normalize_manual_next_step(payload["manual_next_step"])
    if manual_next_step != expected.manual_next_step:
        raise ValueError("manual_next_step must match source evidence fields")
    return payload


def _findings(
    capture: SourceEvidenceCaptureChainGapInput,
) -> tuple[str, tuple[str, ...], str]:
    if capture.official_anchor_present is not True:
        return (
            "blocked",
            ("source_evidence_official_anchor_missing",),
            "manually_capture_official_source_anchor",
        )

    reasons: list[str] = []
    if capture.captured_source_count < capture.expected_source_count:
        reasons.append("source_evidence_captured_count_below_expected")
    if capture.digest_gap_count > ZERO:
        reasons.append("source_evidence_digest_gap_detected")
    if capture.timestamp_gap_count > ZERO:
        reasons.append("source_evidence_timestamp_gap_detected")
    if reasons:
        return (
            "incomplete",
            tuple(reason for reason in REASON_CODE_SEQUENCE if reason in reasons),
            "manually_reconcile_missing_source_evidence",
        )
    return (
        "complete",
        (READY_REASON_CODE,),
        "continue_manual_review_with_captured_evidence",
    )


def _validate_report(report: SourceEvidenceCaptureChainGapReport) -> None:
    source = SourceEvidenceCaptureChainGapInput(
        expected_source_count=report.expected_source_count,
        captured_source_count=report.captured_source_count,
        digest_gap_count=report.digest_gap_count,
        timestamp_gap_count=report.timestamp_gap_count,
        official_anchor_present=report.official_anchor_present,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    status, reason_codes, manual_next_step = _findings(source)
    if report.reason_codes != reason_codes:
        raise ValueError("reason_codes must match source evidence fields")
    if report.capture_chain_status != status:
        raise ValueError("capture_chain_status must match source evidence fields")
    if report.manual_next_step != manual_next_step:
        raise ValueError("manual_next_step must match source evidence fields")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _payload_count(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be serialized as a string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    return _normalize_count(field_name, parsed)


def _normalize_status(value: object) -> str:
    if type(value) is not str or value not in CAPTURE_CHAIN_STATUSES:
        raise ValueError("capture_chain_status must be supported")
    return value


def _normalize_manual_next_step(value: object) -> str:
    if type(value) is not str or value not in MANUAL_NEXT_STEPS:
        raise ValueError("manual_next_step must be supported")
    return value


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    return _normalize_reason_code_items(value)


def _normalize_payload_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is list:
        return _normalize_reason_code_items(tuple(value))
    if type(value) is tuple:
        return _normalize_reason_code_items(value)
    raise ValueError("reason_codes must be a list")


def _normalize_reason_code_items(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in REASON_CODE_SEQUENCE:
            raise ValueError("reason_codes contain unsupported reason code")
        if reason_code in seen:
            raise ValueError("reason_codes must not contain duplicates")
        seen.add(reason_code)
    normalized = tuple(
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in seen
    )
    if reason_codes != normalized:
        raise ValueError("reason_codes must use deterministic sequence")
    return normalized


def _raise_reason_mismatch(expected_reason_codes: tuple[str, ...]) -> None:
    if "source_evidence_official_anchor_missing" in expected_reason_codes:
        raise ValueError("official_anchor_present must match reason_codes")
    if "source_evidence_captured_count_below_expected" in expected_reason_codes:
        raise ValueError("captured_source_count must match reason_codes")
    if "source_evidence_digest_gap_detected" in expected_reason_codes:
        raise ValueError("digest_gap_count must match reason_codes")
    if "source_evidence_timestamp_gap_detected" in expected_reason_codes:
        raise ValueError("timestamp_gap_count must match reason_codes")
    raise ValueError("reason_codes must match source evidence fields")


def _reject_private_public_values(value: object) -> None:
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_private_public_values(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_private_public_values(item)
        return
    if type(value) is str:
        normalized = value.lower()
        if any(fragment in normalized for fragment in PRIVATE_VALUE_FRAGMENTS):
            raise ValueError("public payload contains private value")


def _digest_payload(payload: dict[str, object]) -> str:
    return sha256(
        json.dumps(
            payload,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()
