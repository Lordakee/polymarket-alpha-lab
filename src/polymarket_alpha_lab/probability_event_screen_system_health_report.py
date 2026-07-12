"""Read-only system health report for ProbabilityEventScreen operations."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re


__all__ = (
    "PROBABILITY_EVENT_SCREEN_SYSTEM_HEALTH_REPORT_VERSION",
    "ProbabilityEventScreenSystemHealthInput",
    "ProbabilityEventScreenSystemHealthPublicPayload",
    "ProbabilityEventScreenSystemHealthReport",
    "build_probability_event_screen_system_health_report",
    "probability_event_screen_system_health_report_digest",
    "probability_event_screen_system_health_report_payload",
    "validate_probability_event_screen_system_health_public_payload",
)


PROBABILITY_EVENT_SCREEN_SYSTEM_HEALTH_REPORT_VERSION = (
    "probability-event-screen-system-health-report-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
CHECK_COUNT = Decimal("8.000000")

PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")

CHECK_FIELDS = (
    "acquisition_ready",
    "screening_pipeline_ready",
    "specialist_operating_cycle_ready",
    "operator_runbook_ready",
    "release_gate_ready",
    "learning_dashboard_ready",
    "supabase_persistence_ready",
    "public_payload_safety_ready",
)
BLOCKING_CHECK_FIELDS = (
    "acquisition_ready",
    "screening_pipeline_ready",
    "specialist_operating_cycle_ready",
    "operator_runbook_ready",
    "release_gate_ready",
    "supabase_persistence_ready",
    "public_payload_safety_ready",
)
ATTENTION_CHECK_FIELDS = ("learning_dashboard_ready",)

BLOCKED_REASON_BY_FIELD = {
    "acquisition_ready": "acquisition_not_ready",
    "screening_pipeline_ready": "screening_pipeline_not_ready",
    "specialist_operating_cycle_ready": "specialist_operating_cycle_not_ready",
    "operator_runbook_ready": "operator_runbook_not_ready",
    "release_gate_ready": "release_gate_not_ready",
    "supabase_persistence_ready": "supabase_persistence_not_ready",
    "public_payload_safety_ready": "public_payload_safety_not_ready",
}
ATTENTION_REASON_BY_FIELD = {
    "learning_dashboard_ready": "learning_dashboard_not_ready_attention",
}
READY_REASON = "system_health_ready"
HEALTH_BANDS = ("ready", "watch", "blocked")
BLOCKED_REASON_CODES = tuple(BLOCKED_REASON_BY_FIELD.values()) + (READY_REASON,)
ATTENTION_REASON_CODES = tuple(ATTENTION_REASON_BY_FIELD.values())

PAYLOAD_KEYS = (
    "config_version",
    "system_health_ready",
    "health_band",
    "acquisition_ready",
    "screening_pipeline_ready",
    "specialist_operating_cycle_ready",
    "operator_runbook_ready",
    "release_gate_ready",
    "learning_dashboard_ready",
    "supabase_persistence_ready",
    "public_payload_safety_ready",
    "check_count",
    "ready_check_count",
    "blocked_check_count",
    "attention_check_count",
    "blocked_reason_codes",
    "attention_reason_codes",
    "ready_ratio",
    "paper_only",
    "report_only",
    "readonly",
    "digest",
)


class ProbabilityEventScreenSystemHealthPublicPayload(dict[str, object]):
    """Immutable public payload for this read-only system health report."""

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
class ProbabilityEventScreenSystemHealthInput:
    acquisition_ready: bool
    screening_pipeline_ready: bool
    specialist_operating_cycle_ready: bool
    operator_runbook_ready: bool
    release_gate_ready: bool
    learning_dashboard_ready: bool
    supabase_persistence_ready: bool
    public_payload_safety_ready: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventScreenSystemHealthInput:
            raise TypeError(
                "ProbabilityEventScreenSystemHealthInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventScreenSystemHealthInput:
            raise ValueError(
                "input must be exactly ProbabilityEventScreenSystemHealthInput",
            )
        for field_name in CHECK_FIELDS:
            _require_bool(field_name, getattr(self, field_name))
        _require_hard_flags(self)


@dataclass(frozen=True)
class ProbabilityEventScreenSystemHealthReport:
    config_version: str
    system_health_ready: bool
    health_band: str
    acquisition_ready: bool
    screening_pipeline_ready: bool
    specialist_operating_cycle_ready: bool
    operator_runbook_ready: bool
    release_gate_ready: bool
    learning_dashboard_ready: bool
    supabase_persistence_ready: bool
    public_payload_safety_ready: bool
    check_count: Decimal
    ready_check_count: Decimal
    blocked_check_count: Decimal
    attention_check_count: Decimal
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventScreenSystemHealthReport:
            raise TypeError(
                "ProbabilityEventScreenSystemHealthReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventScreenSystemHealthReport:
            raise ValueError(
                "report must be exactly ProbabilityEventScreenSystemHealthReport",
            )
        _require_public_label("config_version", self.config_version)
        if self.config_version != PROBABILITY_EVENT_SCREEN_SYSTEM_HEALTH_REPORT_VERSION:
            raise ValueError("config_version must be the supported report version")
        _require_bool("system_health_ready", self.system_health_ready)
        _require_health_band("health_band", self.health_band)
        for field_name in CHECK_FIELDS:
            _require_bool(field_name, getattr(self, field_name))
        for field_name in (
            "check_count",
            "ready_check_count",
            "blocked_check_count",
            "attention_check_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
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
    def public_payload(self) -> ProbabilityEventScreenSystemHealthPublicPayload:
        payload = ProbabilityEventScreenSystemHealthPublicPayload(
            _payload_items(self, digest=self.digest),
        )
        validate_probability_event_screen_system_health_public_payload(payload)
        return payload


def build_probability_event_screen_system_health_report(
    inputs: ProbabilityEventScreenSystemHealthInput,
) -> ProbabilityEventScreenSystemHealthReport:
    """Build a deterministic read-only health report over screen subsystems."""

    if type(inputs) is not ProbabilityEventScreenSystemHealthInput:
        raise ValueError(
            "inputs must be a ProbabilityEventScreenSystemHealthInput",
        )
    _require_hard_flags(inputs)
    check_values = {field_name: getattr(inputs, field_name) for field_name in CHECK_FIELDS}
    ready_count = _count(sum(1 for value in check_values.values() if value is True))
    blocked_reason_codes = _blocked_reason_codes(check_values)
    if not blocked_reason_codes:
        blocked_reason_codes = (READY_REASON,)
    attention_reason_codes = _attention_reason_codes(check_values)
    blocked_count = _count(
        sum(
            1
            for field_name in BLOCKING_CHECK_FIELDS
            if check_values[field_name] is not True
        ),
    )
    attention_count = _count(len(attention_reason_codes))
    values: dict[str, object] = {
        "config_version": PROBABILITY_EVENT_SCREEN_SYSTEM_HEALTH_REPORT_VERSION,
        "system_health_ready": blocked_reason_codes == (READY_REASON,),
        "health_band": _health_band(blocked_count, attention_count),
        **check_values,
        "check_count": CHECK_COUNT,
        "ready_check_count": ready_count,
        "blocked_check_count": blocked_count,
        "attention_check_count": attention_count,
        "blocked_reason_codes": blocked_reason_codes,
        "attention_reason_codes": attention_reason_codes,
        "ready_ratio": _ratio(ready_count, CHECK_COUNT),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ProbabilityEventScreenSystemHealthReport(
        **values,
        digest=_payload_digest(_payload_values(values, digest="")),
    )


def probability_event_screen_system_health_report_payload(
    report: ProbabilityEventScreenSystemHealthReport,
) -> ProbabilityEventScreenSystemHealthPublicPayload:
    if type(report) is not ProbabilityEventScreenSystemHealthReport:
        raise ValueError("report must be a ProbabilityEventScreenSystemHealthReport")
    _require_hard_flags(report)
    _validate_report(report)
    expected_digest = probability_event_screen_system_health_report_digest(report)
    if report.digest != expected_digest:
        raise ValueError("digest must match report payload")
    return report.public_payload


def probability_event_screen_system_health_report_digest(
    report: ProbabilityEventScreenSystemHealthReport,
) -> str:
    if type(report) is not ProbabilityEventScreenSystemHealthReport:
        raise ValueError("report must be a ProbabilityEventScreenSystemHealthReport")
    _require_hard_flags(report)
    _validate_report(report)
    return _payload_digest(_payload_items(report, digest=""))


def validate_probability_event_screen_system_health_public_payload(
    payload: Mapping[str, object],
) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    if tuple(payload.keys()) != PAYLOAD_KEYS:
        raise ValueError("payload must match the canonical system health schema")
    _require_public_label("config_version", payload["config_version"])
    if payload["config_version"] != PROBABILITY_EVENT_SCREEN_SYSTEM_HEALTH_REPORT_VERSION:
        raise ValueError("config_version must be the supported report version")
    _require_bool("system_health_ready", payload["system_health_ready"])
    _require_health_band("health_band", payload["health_band"])
    for field_name in (
        *CHECK_FIELDS,
        "paper_only",
        "report_only",
        "readonly",
    ):
        _require_bool(field_name, payload[field_name])
    for flag_name in ("paper_only", "report_only", "readonly"):
        if payload[flag_name] is not True:
            raise ValueError(f"{flag_name} must be True")
    for field_name in (
        "check_count",
        "ready_check_count",
        "blocked_check_count",
        "attention_check_count",
    ):
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


def _validate_report(report: ProbabilityEventScreenSystemHealthReport) -> None:
    check_values = {field_name: getattr(report, field_name) for field_name in CHECK_FIELDS}
    ready_count = _count(sum(1 for value in check_values.values() if value is True))
    blocked_reason_codes = _blocked_reason_codes(check_values)
    if not blocked_reason_codes:
        blocked_reason_codes = (READY_REASON,)
    attention_reason_codes = _attention_reason_codes(check_values)
    blocked_count = _count(
        sum(
            1
            for field_name in BLOCKING_CHECK_FIELDS
            if check_values[field_name] is not True
        ),
    )
    attention_count = _count(len(attention_reason_codes))
    if report.check_count != CHECK_COUNT:
        raise ValueError("check_count must equal canonical check count")
    if report.ready_check_count != ready_count:
        raise ValueError("ready_check_count must match check fields")
    if report.blocked_check_count != blocked_count:
        raise ValueError("blocked_check_count must match check fields")
    if report.attention_check_count != attention_count:
        raise ValueError("attention_check_count must match check fields")
    if report.blocked_reason_codes != blocked_reason_codes:
        raise ValueError("blocked_reason_codes must match check fields")
    if report.attention_reason_codes != attention_reason_codes:
        raise ValueError("attention_reason_codes must match check fields")
    if report.ready_ratio != _ratio(ready_count, report.check_count):
        raise ValueError("ready_ratio must match ready checks")
    if report.system_health_ready != (blocked_reason_codes == (READY_REASON,)):
        raise ValueError("system_health_ready must match blocking checks")
    if report.health_band != _health_band(blocked_count, attention_count):
        raise ValueError("health_band must match canonical readiness band")


def _payload_items(
    report: ProbabilityEventScreenSystemHealthReport,
    *,
    digest: str,
) -> dict[str, object]:
    return _payload_values(_report_values_without_digest(report), digest=digest)


def _report_values_without_digest(
    report: ProbabilityEventScreenSystemHealthReport,
) -> dict[str, object]:
    return {
        "config_version": report.config_version,
        "system_health_ready": report.system_health_ready,
        "health_band": report.health_band,
        "acquisition_ready": report.acquisition_ready,
        "screening_pipeline_ready": report.screening_pipeline_ready,
        "specialist_operating_cycle_ready": report.specialist_operating_cycle_ready,
        "operator_runbook_ready": report.operator_runbook_ready,
        "release_gate_ready": report.release_gate_ready,
        "learning_dashboard_ready": report.learning_dashboard_ready,
        "supabase_persistence_ready": report.supabase_persistence_ready,
        "public_payload_safety_ready": report.public_payload_safety_ready,
        "check_count": report.check_count,
        "ready_check_count": report.ready_check_count,
        "blocked_check_count": report.blocked_check_count,
        "attention_check_count": report.attention_check_count,
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
        "system_health_ready": values["system_health_ready"],
        "health_band": values["health_band"],
        "acquisition_ready": values["acquisition_ready"],
        "screening_pipeline_ready": values["screening_pipeline_ready"],
        "specialist_operating_cycle_ready": values["specialist_operating_cycle_ready"],
        "operator_runbook_ready": values["operator_runbook_ready"],
        "release_gate_ready": values["release_gate_ready"],
        "learning_dashboard_ready": values["learning_dashboard_ready"],
        "supabase_persistence_ready": values["supabase_persistence_ready"],
        "public_payload_safety_ready": values["public_payload_safety_ready"],
        "check_count": _decimal_text(values["check_count"]),
        "ready_check_count": _decimal_text(values["ready_check_count"]),
        "blocked_check_count": _decimal_text(values["blocked_check_count"]),
        "attention_check_count": _decimal_text(values["attention_check_count"]),
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
        for field_name in BLOCKING_CHECK_FIELDS
        if values[field_name] is not True
    )


def _attention_reason_codes(values: Mapping[str, bool]) -> tuple[str, ...]:
    return tuple(
        ATTENTION_REASON_BY_FIELD[field_name]
        for field_name in ATTENTION_CHECK_FIELDS
        if values[field_name] is not True
    )


def _health_band(blocked_count: Decimal, attention_count: Decimal) -> str:
    if blocked_count > ZERO:
        return "blocked"
    if attention_count > ZERO:
        return "watch"
    return "ready"


def _normalize_blocked_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("blocked_reason_codes must be a tuple")
    for reason_code in value:
        if type(reason_code) is not str or reason_code not in BLOCKED_REASON_CODES:
            raise ValueError("blocked_reason_code must be supported")
    if value and READY_REASON in value and value != (READY_REASON,):
        raise ValueError("system health ready reason must stand alone")
    return value


def _normalize_attention_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("attention_reason_codes must be a tuple")
    for reason_code in value:
        if type(reason_code) is not str or reason_code not in ATTENTION_REASON_CODES:
            raise ValueError("attention_reason_code must be supported")
    return value


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = getattr(value, field_name)
        if flag is not True:
            raise ValueError(f"{field_name} must be True")


def _require_public_label(field_name: str, value: object) -> None:
    if type(value) is not str or PUBLIC_LABEL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public label")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be exactly bool")


def _require_health_band(field_name: str, value: object) -> None:
    if type(value) is not str or value not in HEALTH_BANDS:
        raise ValueError(f"{field_name} must be a supported health band")


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
    return format(_require_decimal("payload_decimal", value), "f")


def _payload_digest(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(encoded.encode()).hexdigest()
