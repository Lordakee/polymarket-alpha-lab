"""Pure readonly source-event timeline reconciliation report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence


_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_STATUS_VALUES = frozenset(("pass", "watch", "block"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_REASON_CODE_SEQUENCE = (
    "timeline_timestamp_conflict_detected",
    "timeline_digest_missing",
    "official_timeline_anchor_missing",
    "timeline_point_capture_gap",
    "source_event_timeline_reconciliation_pass",
)
_MANUAL_NEXT_STEPS = frozenset(
    (
        "manual_timeline_timestamp_reconciliation",
        "refresh_timeline_digest_evidence",
        "collect_official_timeline_anchor",
        "review_missing_timeline_points",
        "document_timeline_reconciliation",
    ),
)


@dataclass(frozen=True)
class SourceEventTimelineReconciliationReport:
    expected_timeline_point_count: Decimal
    captured_timeline_point_count: Decimal
    conflicting_timestamp_count: Decimal
    missing_digest_count: Decimal
    official_anchor_present: bool
    reconciliation_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not SourceEventTimelineReconciliationReport:
            raise TypeError(
                "SourceEventTimelineReconciliationReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not SourceEventTimelineReconciliationReport:
            raise ValueError(
                "report must be exactly SourceEventTimelineReconciliationReport",
            )
        for field_name in (
            "expected_timeline_point_count",
            "captured_timeline_point_count",
            "conflicting_timestamp_count",
            "missing_digest_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        _require_bool("official_anchor_present", self.official_anchor_present)
        _require_status("reconciliation_status", self.reconciliation_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_manual_next_step("manual_next_step", self.manual_next_step)
        _require_payload_digest("payload_digest", self.payload_digest)
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        if self.payload_digest != _report_digest(self):
            raise ValueError("payload_digest mismatch")

    @property
    def public_payload(self) -> dict[str, Any]:
        return source_event_timeline_reconciliation_report_payload(self)


def build_source_event_timeline_reconciliation_report(
    *,
    expected_timeline_point_count: Decimal,
    captured_timeline_point_count: Decimal,
    conflicting_timestamp_count: Decimal,
    missing_digest_count: Decimal,
    official_anchor_present: bool,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> SourceEventTimelineReconciliationReport:
    expected_count = _require_count_decimal(
        "expected_timeline_point_count",
        expected_timeline_point_count,
    )
    captured_count = _require_count_decimal(
        "captured_timeline_point_count",
        captured_timeline_point_count,
    )
    conflict_count = _require_count_decimal(
        "conflicting_timestamp_count",
        conflicting_timestamp_count,
    )
    missing_count = _require_count_decimal("missing_digest_count", missing_digest_count)
    _require_bool("official_anchor_present", official_anchor_present)
    flags = _PhaseFlags(paper_only=paper_only, report_only=report_only, readonly=readonly)
    _require_hard_flags("builder", flags)

    reason_codes = _reason_codes(
        expected_timeline_point_count=expected_count,
        captured_timeline_point_count=captured_count,
        conflicting_timestamp_count=conflict_count,
        missing_digest_count=missing_count,
        official_anchor_present=official_anchor_present,
    )
    status = _status(reason_codes)
    manual_next_step = _manual_next_step(reason_codes)
    values: dict[str, Any] = {
        "expected_timeline_point_count": expected_count,
        "captured_timeline_point_count": captured_count,
        "conflicting_timestamp_count": conflict_count,
        "missing_digest_count": missing_count,
        "official_anchor_present": official_anchor_present,
        "reconciliation_status": status,
        "reason_codes": reason_codes,
        "manual_next_step": manual_next_step,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return SourceEventTimelineReconciliationReport(
        **values,
        payload_digest=_digest_from_values(values),
    )


def source_event_timeline_reconciliation_report_payload(
    value: SourceEventTimelineReconciliationReport | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is SourceEventTimelineReconciliationReport:
        _require_hard_flags("report", value)
        payload = _json_ready(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError(
            "value must be a SourceEventTimelineReconciliationReport or dict",
        )
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _verify_payload_digest(payload)
    return payload


@dataclass(frozen=True)
class _PhaseFlags:
    paper_only: bool
    report_only: bool
    readonly: bool


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
    expected_timeline_point_count: Decimal,
    captured_timeline_point_count: Decimal,
    conflicting_timestamp_count: Decimal,
    missing_digest_count: Decimal,
    official_anchor_present: bool,
) -> tuple[str, ...]:
    codes: list[str] = []
    if conflicting_timestamp_count > _ZERO:
        codes.append("timeline_timestamp_conflict_detected")
    if missing_digest_count > _ZERO:
        codes.append("timeline_digest_missing")
    if not official_anchor_present:
        codes.append("official_timeline_anchor_missing")
    if captured_timeline_point_count < expected_timeline_point_count:
        codes.append("timeline_point_capture_gap")
    if not codes:
        codes.append("source_event_timeline_reconciliation_pass")
    return _normalize_reason_codes(codes)


def _status(reason_codes: tuple[str, ...]) -> str:
    if "timeline_timestamp_conflict_detected" in reason_codes:
        return "block"
    if reason_codes != ("source_event_timeline_reconciliation_pass",):
        return "watch"
    return "pass"


def _manual_next_step(reason_codes: tuple[str, ...]) -> str:
    if "timeline_timestamp_conflict_detected" in reason_codes:
        return "manual_timeline_timestamp_reconciliation"
    if "timeline_digest_missing" in reason_codes:
        return "refresh_timeline_digest_evidence"
    if "official_timeline_anchor_missing" in reason_codes:
        return "collect_official_timeline_anchor"
    if "timeline_point_capture_gap" in reason_codes:
        return "review_missing_timeline_points"
    return "document_timeline_reconciliation"


def _validate_report_consistency(report: SourceEventTimelineReconciliationReport) -> None:
    if report.captured_timeline_point_count > report.expected_timeline_point_count:
        raise ValueError(
            "timeline point counts must not exceed expected_timeline_point_count",
        )
    if report.conflicting_timestamp_count > report.expected_timeline_point_count:
        raise ValueError(
            "conflicting_timestamp_count must not exceed expected_timeline_point_count",
        )
    if report.missing_digest_count > report.expected_timeline_point_count:
        raise ValueError(
            "missing_digest_count must not exceed expected_timeline_point_count",
        )
    expected_reasons = _reason_codes(
        expected_timeline_point_count=report.expected_timeline_point_count,
        captured_timeline_point_count=report.captured_timeline_point_count,
        conflicting_timestamp_count=report.conflicting_timestamp_count,
        missing_digest_count=report.missing_digest_count,
        official_anchor_present=report.official_anchor_present,
    )
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match timeline evidence counts")
    if report.reconciliation_status != _status(expected_reasons):
        raise ValueError("reconciliation_status must match reason_codes")
    if report.manual_next_step != _manual_next_step(expected_reasons):
        raise ValueError("manual_next_step must match reason_codes")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if not hasattr(value, field_name):
            raise ValueError(f"{label} must expose {field_name}")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(_QUANT, rounding=ROUND_HALF_UP)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal count")
    return normalized


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUS_VALUES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        if type(reason_code) is not str:
            raise ValueError("reason_code must be a string")
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _require_manual_next_step(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _MANUAL_NEXT_STEPS:
        raise ValueError(f"{field_name} must be supported")


def _require_payload_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _report_digest(report: SourceEventTimelineReconciliationReport) -> str:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    payload.pop("payload_digest", None)
    return _digest_from_values(payload)


def _digest_from_values(values: Mapping[str, Any]) -> str:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    payload.pop("payload_digest", None)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _verify_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("payload_digest")
    _require_payload_digest("payload_digest", digest)
    expected = _digest_from_values(payload)
    if digest != expected:
        raise ValueError("payload_digest mismatch")


def _copy_json_object(value: dict[str, Any]) -> dict[str, Any]:
    ready = _json_ready(value)
    if type(ready) is not dict:
        raise ValueError("public payload must be a JSON object")
    return ready


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value.quantize(_QUANT, rounding=ROUND_HALF_UP))
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object names must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return tuple(_json_ready(item) for item in value)
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


__all__ = (
    "SourceEventTimelineReconciliationReport",
    "build_source_event_timeline_reconciliation_report",
    "source_event_timeline_reconciliation_report_payload",
)
