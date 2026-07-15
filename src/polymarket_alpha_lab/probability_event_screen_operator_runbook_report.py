"""Read-only operator runbook report for probability event screens."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from re import Pattern, compile
from typing import Mapping


__all__ = (
    "OPERATOR_RUNBOOK_BANDS",
    "PROBABILITY_EVENT_SCREEN_OPERATOR_RUNBOOK_REPORT_VERSION",
    "ProbabilityEventScreenOperatorRunbookInput",
    "ProbabilityEventScreenOperatorRunbookReport",
    "build_probability_event_screen_operator_runbook_report",
    "probability_event_screen_operator_runbook_report_payload",
    "probability_event_screen_operator_runbook_report_digest",
)


PROBABILITY_EVENT_SCREEN_OPERATOR_RUNBOOK_REPORT_VERSION = (
    "probability-event-screen-operator-runbook-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TOTAL_SIGNAL_COUNT = Decimal("8").quantize(QUANTUM, rounding=ROUND_HALF_UP)
DIGEST_RE: Pattern[str] = compile(r"^[0-9a-f]{64}$")

BLOCKING_SIGNAL_FIELDS = (
    "dashboard_snapshot_ready",
    "final_review_ready",
    "manual_decision_gate_ready",
    "review_packet_index_ready",
    "exception_queue_ready",
    "supabase_export_manifest_ready",
    "operator_safety_ready",
)
ATTENTION_SIGNAL_FIELDS = ("learning_feedback_ready",)
SIGNAL_FIELDS = (
    "dashboard_snapshot_ready",
    "final_review_ready",
    "manual_decision_gate_ready",
    "review_packet_index_ready",
    "exception_queue_ready",
    "learning_feedback_ready",
    "supabase_export_manifest_ready",
    "operator_safety_ready",
)
OPERATOR_RUNBOOK_BANDS = ("ready", "attention", "blocked")
BLOCKED_REASON_BY_FIELD = {
    "dashboard_snapshot_ready": "dashboard_snapshot_not_ready",
    "final_review_ready": "final_review_not_ready",
    "manual_decision_gate_ready": "manual_decision_gate_not_ready",
    "review_packet_index_ready": "review_packet_index_not_ready",
    "exception_queue_ready": "exception_queue_not_ready",
    "supabase_export_manifest_ready": "supabase_export_manifest_not_ready",
    "operator_safety_ready": "operator_safety_not_ready",
}
ATTENTION_REASON_BY_FIELD = {
    "learning_feedback_ready": "learning_feedback_not_ready",
}
BLOCKED_REASON_CODES = tuple(BLOCKED_REASON_BY_FIELD.values())
ATTENTION_REASON_CODES = tuple(ATTENTION_REASON_BY_FIELD.values())
PAYLOAD_KEYS = (
    "config_version",
    "operator_runbook_ready",
    "runbook_band",
    "dashboard_snapshot_ready",
    "final_review_ready",
    "manual_decision_gate_ready",
    "review_packet_index_ready",
    "exception_queue_ready",
    "learning_feedback_ready",
    "supabase_export_manifest_ready",
    "operator_safety_ready",
    "ready_signal_count",
    "total_signal_count",
    "blocked_reason_codes",
    "attention_reason_codes",
    "ready_ratio",
    "paper_only",
    "report_only",
    "readonly",
    "digest",
)


class ProbabilityEventScreenOperatorRunbookPublicPayload(dict[str, object]):
    """Immutable public payload for the operator runbook report."""

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
class ProbabilityEventScreenOperatorRunbookInput:
    dashboard_snapshot_ready: bool
    final_review_ready: bool
    manual_decision_gate_ready: bool
    review_packet_index_ready: bool
    exception_queue_ready: bool
    learning_feedback_ready: bool
    supabase_export_manifest_ready: bool
    operator_safety_ready: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventScreenOperatorRunbookInput:
            raise TypeError(
                "ProbabilityEventScreenOperatorRunbookInput "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventScreenOperatorRunbookInput:
            raise ValueError(
                "input must be exactly ProbabilityEventScreenOperatorRunbookInput",
            )
        for field_name in SIGNAL_FIELDS:
            _require_bool(field_name, getattr(self, field_name))
        _require_hard_flags(self)


@dataclass(frozen=True)
class ProbabilityEventScreenOperatorRunbookReport:
    config_version: str
    operator_runbook_ready: bool
    runbook_band: str
    dashboard_snapshot_ready: bool
    final_review_ready: bool
    manual_decision_gate_ready: bool
    review_packet_index_ready: bool
    exception_queue_ready: bool
    learning_feedback_ready: bool
    supabase_export_manifest_ready: bool
    operator_safety_ready: bool
    ready_signal_count: Decimal
    total_signal_count: Decimal
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventScreenOperatorRunbookReport:
            raise TypeError(
                "ProbabilityEventScreenOperatorRunbookReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventScreenOperatorRunbookReport:
            raise ValueError(
                "report must be exactly ProbabilityEventScreenOperatorRunbookReport",
            )
        _require_config_version(self.config_version)
        _require_bool("operator_runbook_ready", self.operator_runbook_ready)
        _require_runbook_band(self.runbook_band)
        for field_name in SIGNAL_FIELDS:
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "ready_signal_count",
            _require_count_decimal("ready_signal_count", self.ready_signal_count),
        )
        object.__setattr__(
            self,
            "total_signal_count",
            _require_count_decimal("total_signal_count", self.total_signal_count),
        )
        object.__setattr__(
            self,
            "blocked_reason_codes",
            _normalize_blocked_reason_codes(self.blocked_reason_codes),
        )
        object.__setattr__(
            self,
            "attention_reason_codes",
            _normalize_attention_reason_codes(self.attention_reason_codes),
        )
        object.__setattr__(
            self,
            "ready_ratio",
            _require_ratio_decimal("ready_ratio", self.ready_ratio),
        )
        _require_digest("digest", self.digest)
        _require_hard_flags(self)
        _validate_report(self)
        expected_digest = _payload_digest(_payload_items(self, digest=""))
        if self.digest != expected_digest:
            raise ValueError("digest must match public payload")

    @property
    def public_payload(self) -> ProbabilityEventScreenOperatorRunbookPublicPayload:
        payload = ProbabilityEventScreenOperatorRunbookPublicPayload(
            _payload_items(self, digest=self.digest),
        )
        _validate_public_payload(payload)
        return payload


def build_probability_event_screen_operator_runbook_report(
    inputs: ProbabilityEventScreenOperatorRunbookInput,
) -> ProbabilityEventScreenOperatorRunbookReport:
    """Build a deterministic paper-only operator runbook readiness report."""

    if type(inputs) is not ProbabilityEventScreenOperatorRunbookInput:
        raise ValueError("inputs must be a ProbabilityEventScreenOperatorRunbookInput")
    _require_hard_flags(inputs)
    signal_values = {
        field_name: getattr(inputs, field_name) for field_name in SIGNAL_FIELDS
    }
    blocked_reason_codes = _blocked_reason_codes(signal_values)
    attention_reason_codes = _attention_reason_codes(signal_values)
    runbook_band = _runbook_band(blocked_reason_codes, attention_reason_codes)
    ready_signal_count = _count(
        sum(1 for value in signal_values.values() if value is True),
    )
    values: dict[str, object] = {
        "config_version": PROBABILITY_EVENT_SCREEN_OPERATOR_RUNBOOK_REPORT_VERSION,
        "operator_runbook_ready": runbook_band == "ready",
        "runbook_band": runbook_band,
        **signal_values,
        "ready_signal_count": ready_signal_count,
        "total_signal_count": TOTAL_SIGNAL_COUNT,
        "blocked_reason_codes": blocked_reason_codes,
        "attention_reason_codes": attention_reason_codes,
        "ready_ratio": _ratio(ready_signal_count, TOTAL_SIGNAL_COUNT),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ProbabilityEventScreenOperatorRunbookReport(
        **values,
        digest=_payload_digest(_payload_values(values, digest="")),
    )


def probability_event_screen_operator_runbook_report_payload(
    report: ProbabilityEventScreenOperatorRunbookReport,
) -> ProbabilityEventScreenOperatorRunbookPublicPayload:
    if type(report) is not ProbabilityEventScreenOperatorRunbookReport:
        raise ValueError("report must be a ProbabilityEventScreenOperatorRunbookReport")
    _require_hard_flags(report)
    _validate_report(report)
    expected_digest = probability_event_screen_operator_runbook_report_digest(report)
    if report.digest != expected_digest:
        raise ValueError("digest must match report payload")
    return report.public_payload


def probability_event_screen_operator_runbook_report_digest(
    report: ProbabilityEventScreenOperatorRunbookReport,
) -> str:
    if type(report) is not ProbabilityEventScreenOperatorRunbookReport:
        raise ValueError("report must be a ProbabilityEventScreenOperatorRunbookReport")
    _require_hard_flags(report)
    _validate_report(report)
    return _payload_digest(_payload_items(report, digest=""))


def _validate_report(report: ProbabilityEventScreenOperatorRunbookReport) -> None:
    signal_values = {
        field_name: getattr(report, field_name) for field_name in SIGNAL_FIELDS
    }
    ready_signal_count = _count(
        sum(1 for value in signal_values.values() if value is True),
    )
    blocked_reason_codes = _blocked_reason_codes(signal_values)
    attention_reason_codes = _attention_reason_codes(signal_values)
    runbook_band = _runbook_band(blocked_reason_codes, attention_reason_codes)
    if report.blocked_reason_codes != blocked_reason_codes:
        raise ValueError("blocked_reason_codes must match readiness fields")
    if report.attention_reason_codes != attention_reason_codes:
        raise ValueError("attention_reason_codes must match readiness fields")
    if report.runbook_band != runbook_band:
        raise ValueError("runbook_band must match reason codes")
    if report.operator_runbook_ready != (runbook_band == "ready"):
        raise ValueError("operator_runbook_ready must match runbook band")
    if report.ready_signal_count != ready_signal_count:
        raise ValueError("ready_signal_count must match readiness fields")
    if report.total_signal_count != TOTAL_SIGNAL_COUNT:
        raise ValueError("total_signal_count must match canonical signal count")
    if report.ready_ratio != _ratio(ready_signal_count, report.total_signal_count):
        raise ValueError("ready_ratio must match readiness fields")


def _validate_public_payload(payload: Mapping[str, object]) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    if tuple(payload.keys()) != PAYLOAD_KEYS:
        raise ValueError("payload must match the canonical operator runbook schema")
    _require_config_version(payload["config_version"])
    for field_name in (
        "operator_runbook_ready",
        *SIGNAL_FIELDS,
        "paper_only",
        "report_only",
        "readonly",
    ):
        _require_bool(field_name, payload[field_name])
    for flag_name in ("paper_only", "report_only", "readonly"):
        if payload[flag_name] is not True:
            raise ValueError(f"{flag_name} must be True")
    _require_runbook_band(payload["runbook_band"])
    for field_name in ("ready_signal_count", "total_signal_count"):
        value = payload[field_name]
        if type(value) is not str:
            raise ValueError(f"{field_name} must be serialized as a string")
        _require_count_decimal(field_name, Decimal(value))
    ratio_value = payload["ready_ratio"]
    if type(ratio_value) is not str:
        raise ValueError("ready_ratio must be serialized as a string")
    _require_ratio_decimal("ready_ratio", Decimal(ratio_value))
    blocked_reason_codes = payload["blocked_reason_codes"]
    attention_reason_codes = payload["attention_reason_codes"]
    if type(blocked_reason_codes) is not tuple:
        raise ValueError("blocked_reason_codes must be a tuple")
    if type(attention_reason_codes) is not tuple:
        raise ValueError("attention_reason_codes must be a tuple")
    _normalize_blocked_reason_codes(blocked_reason_codes)
    _normalize_attention_reason_codes(attention_reason_codes)
    digest = payload["digest"]
    _require_digest("digest", digest)
    unsigned = dict(payload)
    unsigned["digest"] = ""
    if digest != _payload_digest(unsigned):
        raise ValueError("digest must match public payload")
    return payload


def _payload_items(
    report: ProbabilityEventScreenOperatorRunbookReport,
    *,
    digest: str,
) -> dict[str, object]:
    return _payload_values(_report_values_without_digest(report), digest=digest)


def _report_values_without_digest(
    report: ProbabilityEventScreenOperatorRunbookReport,
) -> dict[str, object]:
    return {
        "config_version": report.config_version,
        "operator_runbook_ready": report.operator_runbook_ready,
        "runbook_band": report.runbook_band,
        "dashboard_snapshot_ready": report.dashboard_snapshot_ready,
        "final_review_ready": report.final_review_ready,
        "manual_decision_gate_ready": report.manual_decision_gate_ready,
        "review_packet_index_ready": report.review_packet_index_ready,
        "exception_queue_ready": report.exception_queue_ready,
        "learning_feedback_ready": report.learning_feedback_ready,
        "supabase_export_manifest_ready": report.supabase_export_manifest_ready,
        "operator_safety_ready": report.operator_safety_ready,
        "ready_signal_count": report.ready_signal_count,
        "total_signal_count": report.total_signal_count,
        "blocked_reason_codes": report.blocked_reason_codes,
        "attention_reason_codes": report.attention_reason_codes,
        "ready_ratio": report.ready_ratio,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _payload_values(values: Mapping[str, object], *, digest: str) -> dict[str, object]:
    return {
        "config_version": values["config_version"],
        "operator_runbook_ready": values["operator_runbook_ready"],
        "runbook_band": values["runbook_band"],
        "dashboard_snapshot_ready": values["dashboard_snapshot_ready"],
        "final_review_ready": values["final_review_ready"],
        "manual_decision_gate_ready": values["manual_decision_gate_ready"],
        "review_packet_index_ready": values["review_packet_index_ready"],
        "exception_queue_ready": values["exception_queue_ready"],
        "learning_feedback_ready": values["learning_feedback_ready"],
        "supabase_export_manifest_ready": values["supabase_export_manifest_ready"],
        "operator_safety_ready": values["operator_safety_ready"],
        "ready_signal_count": _decimal_text(values["ready_signal_count"]),
        "total_signal_count": _decimal_text(values["total_signal_count"]),
        "blocked_reason_codes": values["blocked_reason_codes"],
        "attention_reason_codes": values["attention_reason_codes"],
        "ready_ratio": _decimal_text(values["ready_ratio"]),
        "paper_only": values["paper_only"],
        "report_only": values["report_only"],
        "readonly": values["readonly"],
        "digest": digest,
    }


def _blocked_reason_codes(values: Mapping[str, bool]) -> tuple[str, ...]:
    return tuple(
        BLOCKED_REASON_BY_FIELD[field_name]
        for field_name in BLOCKING_SIGNAL_FIELDS
        if values[field_name] is not True
    )


def _attention_reason_codes(values: Mapping[str, bool]) -> tuple[str, ...]:
    return tuple(
        ATTENTION_REASON_BY_FIELD[field_name]
        for field_name in ATTENTION_SIGNAL_FIELDS
        if values[field_name] is not True
    )


def _runbook_band(
    blocked_reason_codes: tuple[str, ...],
    attention_reason_codes: tuple[str, ...],
) -> str:
    if blocked_reason_codes:
        return "blocked"
    if attention_reason_codes:
        return "attention"
    return "ready"


def _normalize_blocked_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("blocked_reason_codes must be a tuple")
    expected = tuple(reason for reason in BLOCKED_REASON_CODES if reason in value)
    if value != expected:
        raise ValueError("blocked_reason_codes must be sorted and unique")
    for reason_code in value:
        if type(reason_code) is not str or reason_code not in BLOCKED_REASON_CODES:
            raise ValueError("blocked_reason_code must be supported")
    return value


def _normalize_attention_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("attention_reason_codes must be a tuple")
    expected = tuple(reason for reason in ATTENTION_REASON_CODES if reason in value)
    if value != expected:
        raise ValueError("attention_reason_codes must be sorted and unique")
    for reason_code in value:
        if type(reason_code) is not str or reason_code not in ATTENTION_REASON_CODES:
            raise ValueError("attention_reason_code must be supported")
    return value


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = getattr(value, field_name)
        if flag is not True:
            raise ValueError(f"{field_name} must be True")


def _require_config_version(value: object) -> None:
    if value != PROBABILITY_EVENT_SCREEN_OPERATOR_RUNBOOK_REPORT_VERSION:
        raise ValueError("config_version must be the supported report version")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be exactly bool")


def _require_runbook_band(value: object) -> None:
    if type(value) is not str or value not in OPERATOR_RUNBOOK_BANDS:
        raise ValueError("runbook_band must be supported")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
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


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count source must be a nonnegative int")
    return Decimal(value).quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _require_ratio_decimal("ready_ratio", numerator / denominator)


def _decimal_text(value: object) -> str:
    if type(value) is not Decimal:
        raise ValueError("public numeric value must be Decimal")
    return format(value.quantize(QUANTUM, rounding=ROUND_HALF_UP), "f")


def _payload_digest(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=_json_default,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_default(value: object) -> object:
    if type(value) is tuple:
        return list(value)
    raise TypeError(f"value is not JSON serializable: {value!r}")
