"""Read-only export manifest readiness report for ProbabilityEventScreen."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re


__all__ = (
    "PROBABILITY_EVENT_SCREEN_EXPORT_MANIFEST_REPORT_VERSION",
    "ProbabilityEventScreenExportManifestInput",
    "ProbabilityEventScreenExportManifestPublicPayload",
    "ProbabilityEventScreenExportManifestReport",
    "build_probability_event_screen_export_manifest_report",
    "probability_event_screen_export_manifest_report_digest",
    "probability_event_screen_export_manifest_report_payload",
)


PROBABILITY_EVENT_SCREEN_EXPORT_MANIFEST_REPORT_VERSION = (
    "probability-event-screen-export-manifest-report-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
ARTIFACT_COUNT = Decimal("8.000000")

PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")

ARTIFACT_FIELDS = (
    "screen_digest_present",
    "recommendation_digest_present",
    "research_packet_digest_present",
    "operator_safety_digest_present",
    "supabase_contract_ready",
    "redacted_payload_ready",
    "ephemeral_log_excluded",
    "manual_review_trace_ready",
)
BLOCKING_ARTIFACT_FIELDS = (
    "screen_digest_present",
    "recommendation_digest_present",
    "research_packet_digest_present",
    "operator_safety_digest_present",
    "supabase_contract_ready",
    "redacted_payload_ready",
    "manual_review_trace_ready",
)
ATTENTION_ARTIFACT_FIELDS = ("ephemeral_log_excluded",)

BLOCKED_REASON_BY_FIELD = {
    "screen_digest_present": "screen_digest_missing",
    "recommendation_digest_present": "recommendation_digest_missing",
    "research_packet_digest_present": "research_packet_digest_missing",
    "operator_safety_digest_present": "operator_safety_digest_missing",
    "supabase_contract_ready": "supabase_contract_not_ready",
    "redacted_payload_ready": "redacted_payload_not_ready",
    "manual_review_trace_ready": "manual_review_trace_missing",
}
ATTENTION_REASON_BY_FIELD = {
    "ephemeral_log_excluded": "ephemeral_log_included_attention",
}
READY_REASON = "export_manifest_ready"
BLOCKED_REASON_CODES = tuple(BLOCKED_REASON_BY_FIELD.values()) + (READY_REASON,)
ATTENTION_REASON_CODES = tuple(ATTENTION_REASON_BY_FIELD.values())

PAYLOAD_KEYS = (
    "config_version",
    "export_manifest_ready",
    "screen_digest_present",
    "recommendation_digest_present",
    "research_packet_digest_present",
    "operator_safety_digest_present",
    "supabase_contract_ready",
    "redacted_payload_ready",
    "ephemeral_log_excluded",
    "manual_review_trace_ready",
    "artifact_count",
    "present_artifact_count",
    "missing_artifact_count",
    "blocked_reason_codes",
    "attention_reason_codes",
    "ready_ratio",
    "paper_only",
    "report_only",
    "readonly",
    "digest",
)


class ProbabilityEventScreenExportManifestPublicPayload(dict[str, object]):
    """Immutable public payload for this read-only manifest report."""

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
class ProbabilityEventScreenExportManifestInput:
    screen_digest_present: bool
    recommendation_digest_present: bool
    research_packet_digest_present: bool
    operator_safety_digest_present: bool
    supabase_contract_ready: bool
    redacted_payload_ready: bool
    ephemeral_log_excluded: bool
    manual_review_trace_ready: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventScreenExportManifestInput:
            raise TypeError(
                "ProbabilityEventScreenExportManifestInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventScreenExportManifestInput:
            raise ValueError(
                "input must be exactly ProbabilityEventScreenExportManifestInput",
            )
        for field_name in ARTIFACT_FIELDS:
            _require_bool(field_name, getattr(self, field_name))
        _require_hard_flags(self)


@dataclass(frozen=True)
class ProbabilityEventScreenExportManifestReport:
    config_version: str
    export_manifest_ready: bool
    screen_digest_present: bool
    recommendation_digest_present: bool
    research_packet_digest_present: bool
    operator_safety_digest_present: bool
    supabase_contract_ready: bool
    redacted_payload_ready: bool
    ephemeral_log_excluded: bool
    manual_review_trace_ready: bool
    artifact_count: Decimal
    present_artifact_count: Decimal
    missing_artifact_count: Decimal
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventScreenExportManifestReport:
            raise TypeError(
                "ProbabilityEventScreenExportManifestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventScreenExportManifestReport:
            raise ValueError(
                "report must be exactly ProbabilityEventScreenExportManifestReport",
            )
        _require_public_label("config_version", self.config_version)
        if self.config_version != PROBABILITY_EVENT_SCREEN_EXPORT_MANIFEST_REPORT_VERSION:
            raise ValueError("config_version must be the supported report version")
        _require_bool("export_manifest_ready", self.export_manifest_ready)
        for field_name in ARTIFACT_FIELDS:
            _require_bool(field_name, getattr(self, field_name))
        for field_name in (
            "artifact_count",
            "present_artifact_count",
            "missing_artifact_count",
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
    def public_payload(self) -> ProbabilityEventScreenExportManifestPublicPayload:
        payload = ProbabilityEventScreenExportManifestPublicPayload(
            _payload_items(self, digest=self.digest),
        )
        _validate_public_payload(payload)
        return payload


def build_probability_event_screen_export_manifest_report(
    inputs: ProbabilityEventScreenExportManifestInput,
) -> ProbabilityEventScreenExportManifestReport:
    """Build a deterministic read-only export manifest readiness report."""

    if type(inputs) is not ProbabilityEventScreenExportManifestInput:
        raise ValueError(
            "inputs must be a ProbabilityEventScreenExportManifestInput",
        )
    _require_hard_flags(inputs)
    artifact_values = {
        field_name: getattr(inputs, field_name) for field_name in ARTIFACT_FIELDS
    }
    present_count = _count(sum(1 for value in artifact_values.values() if value is True))
    missing_count = _count(
        sum(1 for value in artifact_values.values() if value is not True),
    )
    blocked_reason_codes = _blocked_reason_codes(artifact_values)
    if not blocked_reason_codes:
        blocked_reason_codes = (READY_REASON,)
    values: dict[str, object] = {
        "config_version": PROBABILITY_EVENT_SCREEN_EXPORT_MANIFEST_REPORT_VERSION,
        "export_manifest_ready": blocked_reason_codes == (READY_REASON,),
        **artifact_values,
        "artifact_count": ARTIFACT_COUNT,
        "present_artifact_count": present_count,
        "missing_artifact_count": missing_count,
        "blocked_reason_codes": blocked_reason_codes,
        "attention_reason_codes": _attention_reason_codes(artifact_values),
        "ready_ratio": _ratio(present_count, ARTIFACT_COUNT),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ProbabilityEventScreenExportManifestReport(
        **values,
        digest=_payload_digest(_payload_values(values, digest="")),
    )


def probability_event_screen_export_manifest_report_payload(
    report: ProbabilityEventScreenExportManifestReport,
) -> ProbabilityEventScreenExportManifestPublicPayload:
    if type(report) is not ProbabilityEventScreenExportManifestReport:
        raise ValueError("report must be a ProbabilityEventScreenExportManifestReport")
    _require_hard_flags(report)
    _validate_report(report)
    expected_digest = probability_event_screen_export_manifest_report_digest(report)
    if report.digest != expected_digest:
        raise ValueError("digest must match report payload")
    return report.public_payload


def probability_event_screen_export_manifest_report_digest(
    report: ProbabilityEventScreenExportManifestReport,
) -> str:
    if type(report) is not ProbabilityEventScreenExportManifestReport:
        raise ValueError("report must be a ProbabilityEventScreenExportManifestReport")
    _require_hard_flags(report)
    _validate_report(report)
    return _payload_digest(_payload_items(report, digest=""))


def _validate_report(report: ProbabilityEventScreenExportManifestReport) -> None:
    artifact_values = {
        field_name: getattr(report, field_name) for field_name in ARTIFACT_FIELDS
    }
    present_count = _count(sum(1 for value in artifact_values.values() if value is True))
    missing_count = _count(
        sum(1 for value in artifact_values.values() if value is not True),
    )
    blocked_reason_codes = _blocked_reason_codes(artifact_values)
    if not blocked_reason_codes:
        blocked_reason_codes = (READY_REASON,)
    if report.artifact_count != ARTIFACT_COUNT:
        raise ValueError("artifact_count must equal canonical artifact count")
    if report.present_artifact_count != present_count:
        raise ValueError("present_artifact_count must match artifact fields")
    if report.missing_artifact_count != missing_count:
        raise ValueError("missing_artifact_count must match artifact fields")
    if report.blocked_reason_codes != blocked_reason_codes:
        raise ValueError("blocked_reason_codes must match artifact fields")
    if report.attention_reason_codes != _attention_reason_codes(artifact_values):
        raise ValueError("attention_reason_codes must match artifact fields")
    if report.ready_ratio != _ratio(present_count, report.artifact_count):
        raise ValueError("ready_ratio must match present artifacts")
    if report.export_manifest_ready != (blocked_reason_codes == (READY_REASON,)):
        raise ValueError("export_manifest_ready must match blocking artifacts")


def _validate_public_payload(
    payload: Mapping[str, object],
) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    if tuple(payload.keys()) != PAYLOAD_KEYS:
        raise ValueError("payload must match the canonical export manifest schema")
    _require_public_label("config_version", payload["config_version"])
    if payload["config_version"] != PROBABILITY_EVENT_SCREEN_EXPORT_MANIFEST_REPORT_VERSION:
        raise ValueError("config_version must be the supported report version")
    for field_name in (
        "export_manifest_ready",
        *ARTIFACT_FIELDS,
        "paper_only",
        "report_only",
        "readonly",
    ):
        _require_bool(field_name, payload[field_name])
    for flag_name in ("paper_only", "report_only", "readonly"):
        if payload[flag_name] is not True:
            raise ValueError(f"{flag_name} must be True")
    for field_name in (
        "artifact_count",
        "present_artifact_count",
        "missing_artifact_count",
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


def _payload_items(
    report: ProbabilityEventScreenExportManifestReport,
    *,
    digest: str,
) -> dict[str, object]:
    return _payload_values(_report_values_without_digest(report), digest=digest)


def _report_values_without_digest(
    report: ProbabilityEventScreenExportManifestReport,
) -> dict[str, object]:
    return {
        "config_version": report.config_version,
        "export_manifest_ready": report.export_manifest_ready,
        "screen_digest_present": report.screen_digest_present,
        "recommendation_digest_present": report.recommendation_digest_present,
        "research_packet_digest_present": report.research_packet_digest_present,
        "operator_safety_digest_present": report.operator_safety_digest_present,
        "supabase_contract_ready": report.supabase_contract_ready,
        "redacted_payload_ready": report.redacted_payload_ready,
        "ephemeral_log_excluded": report.ephemeral_log_excluded,
        "manual_review_trace_ready": report.manual_review_trace_ready,
        "artifact_count": report.artifact_count,
        "present_artifact_count": report.present_artifact_count,
        "missing_artifact_count": report.missing_artifact_count,
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
        "export_manifest_ready": values["export_manifest_ready"],
        "screen_digest_present": values["screen_digest_present"],
        "recommendation_digest_present": values["recommendation_digest_present"],
        "research_packet_digest_present": values["research_packet_digest_present"],
        "operator_safety_digest_present": values["operator_safety_digest_present"],
        "supabase_contract_ready": values["supabase_contract_ready"],
        "redacted_payload_ready": values["redacted_payload_ready"],
        "ephemeral_log_excluded": values["ephemeral_log_excluded"],
        "manual_review_trace_ready": values["manual_review_trace_ready"],
        "artifact_count": _decimal_text(values["artifact_count"]),
        "present_artifact_count": _decimal_text(values["present_artifact_count"]),
        "missing_artifact_count": _decimal_text(values["missing_artifact_count"]),
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
        for field_name in BLOCKING_ARTIFACT_FIELDS
        if values[field_name] is not True
    )


def _attention_reason_codes(values: Mapping[str, bool]) -> tuple[str, ...]:
    return tuple(
        ATTENTION_REASON_BY_FIELD[field_name]
        for field_name in ATTENTION_ARTIFACT_FIELDS
        if values[field_name] is not True
    )


def _normalize_blocked_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("blocked_reason_codes must be a tuple")
    for reason_code in value:
        if type(reason_code) is not str or reason_code not in BLOCKED_REASON_CODES:
            raise ValueError("blocked_reason_code must be supported")
    if value and READY_REASON in value and value != (READY_REASON,):
        raise ValueError("export manifest ready reason must stand alone")
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
    raise TypeError(f"unsupported public payload value: {value!r}")
