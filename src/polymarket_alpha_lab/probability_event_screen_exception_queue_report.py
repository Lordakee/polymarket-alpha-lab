"""Pure paper-only probability event screen exception queue report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from typing import Any, Mapping, Sequence


_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SEVERITY_BANDS = frozenset(("ready", "attention", "blocked"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_REASON_CODE_SEQUENCE = (
    "manual_review_capacity_not_ready",
    "operator_safety_not_ready",
    "unsafe_payload_present",
    "conflicting_evidence_present",
    "liquidity_blocked_present",
    "missing_digest_present",
    "stale_source_present",
)


@dataclass(frozen=True)
class ProbabilityEventScreenExceptionQueueReport:
    total_exception_count: Decimal
    unsafe_payload_count: Decimal
    missing_digest_count: Decimal
    stale_source_count: Decimal
    conflicting_evidence_count: Decimal
    liquidity_blocked_count: Decimal
    manual_review_capacity_ready: bool
    operator_safety_ready: bool
    exception_queue_ready: bool
    exception_severity_band: str
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "total_exception_count",
            "unsafe_payload_count",
            "missing_digest_count",
            "stale_source_count",
            "conflicting_evidence_count",
            "liquidity_blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        _require_bool("manual_review_capacity_ready", self.manual_review_capacity_ready)
        _require_bool("operator_safety_ready", self.operator_safety_ready)
        _require_bool("exception_queue_ready", self.exception_queue_ready)
        _require_severity_band("exception_severity_band", self.exception_severity_band)
        object.__setattr__(
            self,
            "blocked_reason_codes",
            _normalize_reason_codes(self.blocked_reason_codes),
        )
        object.__setattr__(
            self,
            "attention_reason_codes",
            _normalize_reason_codes(self.attention_reason_codes),
        )
        object.__setattr__(
            self,
            "ready_ratio",
            _require_ratio_decimal("ready_ratio", self.ready_ratio),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)

    @property
    def public_payload(self) -> dict[str, Any]:
        payload = _payload_without_digest(self)
        payload["digest"] = self.digest
        return payload

    @property
    def digest(self) -> str:
        canonical = json.dumps(
            _payload_without_digest(self),
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_probability_event_screen_exception_queue_report(
    *,
    total_exception_count: Decimal,
    unsafe_payload_count: Decimal,
    missing_digest_count: Decimal,
    stale_source_count: Decimal,
    conflicting_evidence_count: Decimal,
    liquidity_blocked_count: Decimal,
    manual_review_capacity_ready: bool,
    operator_safety_ready: bool,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ProbabilityEventScreenExceptionQueueReport:
    total = _require_count_decimal("total_exception_count", total_exception_count)
    unsafe = _require_count_decimal("unsafe_payload_count", unsafe_payload_count)
    missing_digest = _require_count_decimal("missing_digest_count", missing_digest_count)
    stale_source = _require_count_decimal("stale_source_count", stale_source_count)
    conflicting = _require_count_decimal(
        "conflicting_evidence_count",
        conflicting_evidence_count,
    )
    liquidity_blocked = _require_count_decimal(
        "liquidity_blocked_count",
        liquidity_blocked_count,
    )
    _require_bool("manual_review_capacity_ready", manual_review_capacity_ready)
    _require_bool("operator_safety_ready", operator_safety_ready)
    flags = _PhaseFlags(paper_only=paper_only, report_only=report_only, readonly=readonly)
    _require_hard_flags("builder", flags)
    _require_exception_counts(
        total,
        unsafe,
        missing_digest,
        stale_source,
        conflicting,
        liquidity_blocked,
    )

    blocked_reasons = _blocked_reason_codes(
        manual_review_capacity_ready=manual_review_capacity_ready,
        operator_safety_ready=operator_safety_ready,
        unsafe_payload_count=unsafe,
    )
    attention_reasons = _attention_reason_codes(
        missing_digest_count=missing_digest,
        stale_source_count=stale_source,
        conflicting_evidence_count=conflicting,
        liquidity_blocked_count=liquidity_blocked,
    )
    severity_band = _severity_band(blocked_reasons, attention_reasons)
    return ProbabilityEventScreenExceptionQueueReport(
        total_exception_count=total,
        unsafe_payload_count=unsafe,
        missing_digest_count=missing_digest,
        stale_source_count=stale_source,
        conflicting_evidence_count=conflicting,
        liquidity_blocked_count=liquidity_blocked,
        manual_review_capacity_ready=manual_review_capacity_ready,
        operator_safety_ready=operator_safety_ready,
        exception_queue_ready=severity_band == "ready",
        exception_severity_band=severity_band,
        blocked_reason_codes=blocked_reasons,
        attention_reason_codes=attention_reasons,
        ready_ratio=_ready_ratio(
            severity_band=severity_band,
            total_exception_count=total,
            exception_reason_count=_exception_reason_count(
                unsafe,
                missing_digest,
                stale_source,
                conflicting,
                liquidity_blocked,
            ),
        ),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def probability_event_screen_exception_queue_report_payload(
    report: ProbabilityEventScreenExceptionQueueReport,
) -> dict[str, Any]:
    if type(report) is not ProbabilityEventScreenExceptionQueueReport:
        raise ValueError("report must be a ProbabilityEventScreenExceptionQueueReport")
    return report.public_payload


@dataclass(frozen=True)
class _PhaseFlags:
    paper_only: bool
    report_only: bool
    readonly: bool


def _blocked_reason_codes(
    *,
    manual_review_capacity_ready: bool,
    operator_safety_ready: bool,
    unsafe_payload_count: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if not manual_review_capacity_ready:
        reason_codes.append("manual_review_capacity_not_ready")
    if not operator_safety_ready:
        reason_codes.append("operator_safety_not_ready")
    if unsafe_payload_count > _ZERO:
        reason_codes.append("unsafe_payload_present")
    return _normalize_reason_codes(reason_codes)


def _attention_reason_codes(
    *,
    missing_digest_count: Decimal,
    stale_source_count: Decimal,
    conflicting_evidence_count: Decimal,
    liquidity_blocked_count: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if conflicting_evidence_count > _ZERO:
        reason_codes.append("conflicting_evidence_present")
    if liquidity_blocked_count > _ZERO:
        reason_codes.append("liquidity_blocked_present")
    if missing_digest_count > _ZERO:
        reason_codes.append("missing_digest_present")
    if stale_source_count > _ZERO:
        reason_codes.append("stale_source_present")
    return _normalize_reason_codes(reason_codes)


def _severity_band(
    blocked_reason_codes: tuple[str, ...],
    attention_reason_codes: tuple[str, ...],
) -> str:
    if blocked_reason_codes:
        return "blocked"
    if attention_reason_codes:
        return "attention"
    return "ready"


def _ready_ratio(
    *,
    severity_band: str,
    total_exception_count: Decimal,
    exception_reason_count: Decimal,
) -> Decimal:
    if total_exception_count == _ZERO:
        return _ZERO
    if severity_band == "blocked":
        return _ZERO
    ready_count = total_exception_count - exception_reason_count
    if ready_count < _ZERO:
        return _ZERO
    return _quantize(ready_count / total_exception_count)


def _validate_report_consistency(
    report: ProbabilityEventScreenExceptionQueueReport,
) -> None:
    _require_exception_counts(
        report.total_exception_count,
        report.unsafe_payload_count,
        report.missing_digest_count,
        report.stale_source_count,
        report.conflicting_evidence_count,
        report.liquidity_blocked_count,
    )
    expected_blocked_reasons = _blocked_reason_codes(
        manual_review_capacity_ready=report.manual_review_capacity_ready,
        operator_safety_ready=report.operator_safety_ready,
        unsafe_payload_count=report.unsafe_payload_count,
    )
    if report.blocked_reason_codes != expected_blocked_reasons:
        raise ValueError("blocked_reason_codes must match report inputs")
    expected_attention_reasons = _attention_reason_codes(
        missing_digest_count=report.missing_digest_count,
        stale_source_count=report.stale_source_count,
        conflicting_evidence_count=report.conflicting_evidence_count,
        liquidity_blocked_count=report.liquidity_blocked_count,
    )
    if report.attention_reason_codes != expected_attention_reasons:
        raise ValueError("attention_reason_codes must match report inputs")
    expected_band = _severity_band(expected_blocked_reasons, expected_attention_reasons)
    if report.exception_severity_band != expected_band:
        raise ValueError("exception_severity_band must match report inputs")
    expected_ready = expected_band == "ready"
    if report.exception_queue_ready is not expected_ready:
        raise ValueError("exception_queue_ready must match report inputs")
    if report.ready_ratio != _ready_ratio(
        severity_band=expected_band,
        total_exception_count=report.total_exception_count,
        exception_reason_count=_exception_reason_count(
            report.unsafe_payload_count,
            report.missing_digest_count,
            report.stale_source_count,
            report.conflicting_evidence_count,
            report.liquidity_blocked_count,
        ),
    ):
        raise ValueError("ready_ratio must match report inputs")


def _exception_reason_count(
    unsafe_payload_count: Decimal,
    missing_digest_count: Decimal,
    stale_source_count: Decimal,
    conflicting_evidence_count: Decimal,
    liquidity_blocked_count: Decimal,
) -> Decimal:
    return (
        unsafe_payload_count
        + missing_digest_count
        + stale_source_count
        + conflicting_evidence_count
        + liquidity_blocked_count
    )


def _require_exception_counts(
    total_exception_count: Decimal,
    unsafe_payload_count: Decimal,
    missing_digest_count: Decimal,
    stale_source_count: Decimal,
    conflicting_evidence_count: Decimal,
    liquidity_blocked_count: Decimal,
) -> None:
    if (
        _exception_reason_count(
            unsafe_payload_count,
            missing_digest_count,
            stale_source_count,
            conflicting_evidence_count,
            liquidity_blocked_count,
        )
        > total_exception_count
    ):
        raise ValueError("exception counts must not exceed total_exception_count")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if not hasattr(value, field_name):
            raise ValueError(f"{label} must expose {field_name}")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_severity_band(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _SEVERITY_BANDS:
        raise ValueError(f"{field_name} must be ready, attention, or blocked")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal count")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


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


def _payload_without_digest(
    report: ProbabilityEventScreenExceptionQueueReport,
) -> dict[str, Any]:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    return payload


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


__all__ = (
    "ProbabilityEventScreenExceptionQueueReport",
    "build_probability_event_screen_exception_queue_report",
    "probability_event_screen_exception_queue_report_payload",
)
