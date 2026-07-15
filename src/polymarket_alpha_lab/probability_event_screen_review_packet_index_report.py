"""Read-only review packet index readiness report for ProbabilityEventScreen."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re


__all__ = (
    "PROBABILITY_EVENT_SCREEN_REVIEW_PACKET_INDEX_REPORT_VERSION",
    "ProbabilityEventScreenReviewPacketIndexInput",
    "ProbabilityEventScreenReviewPacketIndexPublicPayload",
    "ProbabilityEventScreenReviewPacketIndexReport",
    "build_probability_event_screen_review_packet_index_report",
    "probability_event_screen_review_packet_index_report_digest",
    "probability_event_screen_review_packet_index_report_payload",
)


PROBABILITY_EVENT_SCREEN_REVIEW_PACKET_INDEX_REPORT_VERSION = (
    "probability-event-screen-review-packet-index-report-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
ARTIFACT_COUNT = Decimal("8.000000")

PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")

ARTIFACT_FIELDS = (
    "screen_digest_present",
    "research_packet_digest_present",
    "source_reliability_digest_present",
    "due_diligence_digest_present",
    "quality_index_digest_present",
    "decision_memo_digest_present",
    "export_manifest_digest_present",
    "operator_safety_digest_present",
)

BLOCKED_REASON_BY_FIELD = {
    "screen_digest_present": "screen_digest_missing",
    "research_packet_digest_present": "research_packet_digest_missing",
    "source_reliability_digest_present": "source_reliability_digest_missing",
    "due_diligence_digest_present": "due_diligence_digest_missing",
    "quality_index_digest_present": "quality_index_digest_missing",
    "decision_memo_digest_present": "decision_memo_digest_missing",
    "export_manifest_digest_present": "export_manifest_digest_missing",
    "operator_safety_digest_present": "operator_safety_digest_missing",
}
READY_REASON = "review_packet_index_ready"
INCOMPLETE_ATTENTION_REASON = "review_packet_index_incomplete_attention"
OPERATOR_SAFETY_ATTENTION_REASON = "operator_safety_digest_missing_attention"
BLOCKED_REASON_CODES = tuple(BLOCKED_REASON_BY_FIELD.values()) + (READY_REASON,)
ATTENTION_REASON_CODES = (
    OPERATOR_SAFETY_ATTENTION_REASON,
    INCOMPLETE_ATTENTION_REASON,
)

PAYLOAD_KEYS = (
    "config_version",
    "review_packet_index_ready",
    *ARTIFACT_FIELDS,
    "artifact_count",
    "present_artifact_count",
    "missing_artifact_count",
    "index_completeness_score",
    "blocked_reason_codes",
    "attention_reason_codes",
    "ready_ratio",
    "paper_only",
    "report_only",
    "readonly",
    "digest",
)


class ProbabilityEventScreenReviewPacketIndexPublicPayload(dict[str, object]):
    """Immutable public payload for this read-only index report."""

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
class ProbabilityEventScreenReviewPacketIndexInput:
    screen_digest_present: bool
    research_packet_digest_present: bool
    source_reliability_digest_present: bool
    due_diligence_digest_present: bool
    quality_index_digest_present: bool
    decision_memo_digest_present: bool
    export_manifest_digest_present: bool
    operator_safety_digest_present: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventScreenReviewPacketIndexInput:
            raise TypeError(
                "ProbabilityEventScreenReviewPacketIndexInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventScreenReviewPacketIndexInput:
            raise ValueError(
                "input must be exactly ProbabilityEventScreenReviewPacketIndexInput",
            )
        for field_name in ARTIFACT_FIELDS:
            _require_bool(field_name, getattr(self, field_name))
        _require_hard_flags(self)


@dataclass(frozen=True)
class ProbabilityEventScreenReviewPacketIndexReport:
    config_version: str
    review_packet_index_ready: bool
    screen_digest_present: bool
    research_packet_digest_present: bool
    source_reliability_digest_present: bool
    due_diligence_digest_present: bool
    quality_index_digest_present: bool
    decision_memo_digest_present: bool
    export_manifest_digest_present: bool
    operator_safety_digest_present: bool
    artifact_count: Decimal
    present_artifact_count: Decimal
    missing_artifact_count: Decimal
    index_completeness_score: Decimal
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventScreenReviewPacketIndexReport:
            raise TypeError(
                "ProbabilityEventScreenReviewPacketIndexReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventScreenReviewPacketIndexReport:
            raise ValueError(
                "report must be exactly ProbabilityEventScreenReviewPacketIndexReport",
            )
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != PROBABILITY_EVENT_SCREEN_REVIEW_PACKET_INDEX_REPORT_VERSION
        ):
            raise ValueError("config_version must be the supported report version")
        _require_bool("review_packet_index_ready", self.review_packet_index_ready)
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
            "index_completeness_score",
            _require_ratio_decimal(
                "index_completeness_score",
                self.index_completeness_score,
            ),
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
        _require_hard_flags(self)
        _require_digest("digest", self.digest)
        _validate_report(self)
        expected_digest = _payload_digest(_payload_items(self, digest=""))
        if self.digest != expected_digest:
            raise ValueError("digest must match public payload")

    @property
    def public_payload(self) -> ProbabilityEventScreenReviewPacketIndexPublicPayload:
        payload = ProbabilityEventScreenReviewPacketIndexPublicPayload(
            _payload_items(self, digest=self.digest),
        )
        _validate_public_payload(payload)
        return payload


def build_probability_event_screen_review_packet_index_report(
    inputs: ProbabilityEventScreenReviewPacketIndexInput,
) -> ProbabilityEventScreenReviewPacketIndexReport:
    """Build a deterministic review packet index readiness report."""

    if type(inputs) is not ProbabilityEventScreenReviewPacketIndexInput:
        raise ValueError(
            "inputs must be a ProbabilityEventScreenReviewPacketIndexInput",
        )
    _require_hard_flags(inputs)
    artifact_values = {
        field_name: getattr(inputs, field_name) for field_name in ARTIFACT_FIELDS
    }
    present_count = _count(sum(1 for value in artifact_values.values() if value is True))
    missing_count = _count(
        sum(1 for value in artifact_values.values() if value is not True),
    )
    completeness_score = _ratio(present_count, ARTIFACT_COUNT)
    blocked_reason_codes = _blocked_reason_codes(artifact_values)
    if not blocked_reason_codes:
        blocked_reason_codes = (READY_REASON,)
    values: dict[str, object] = {
        "config_version": PROBABILITY_EVENT_SCREEN_REVIEW_PACKET_INDEX_REPORT_VERSION,
        "review_packet_index_ready": blocked_reason_codes == (READY_REASON,),
        **artifact_values,
        "artifact_count": ARTIFACT_COUNT,
        "present_artifact_count": present_count,
        "missing_artifact_count": missing_count,
        "index_completeness_score": completeness_score,
        "blocked_reason_codes": blocked_reason_codes,
        "attention_reason_codes": _attention_reason_codes(artifact_values),
        "ready_ratio": completeness_score,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ProbabilityEventScreenReviewPacketIndexReport(
        **values,
        digest=_payload_digest(_coerce_payload_values(values | {"digest": ""})),
    )


def probability_event_screen_review_packet_index_report_payload(
    report: ProbabilityEventScreenReviewPacketIndexReport | Mapping[str, object],
) -> ProbabilityEventScreenReviewPacketIndexPublicPayload:
    if type(report) is ProbabilityEventScreenReviewPacketIndexReport:
        _require_hard_flags(report)
        payload = report.public_payload
    elif isinstance(report, Mapping):
        payload = ProbabilityEventScreenReviewPacketIndexPublicPayload(report)
    else:
        raise ValueError(
            "report must be a ProbabilityEventScreenReviewPacketIndexReport",
        )
    _validate_public_payload(payload)
    return payload


def probability_event_screen_review_packet_index_report_digest(
    report: ProbabilityEventScreenReviewPacketIndexReport | Mapping[str, object],
) -> str:
    payload = probability_event_screen_review_packet_index_report_payload(report)
    digest = payload["digest"]
    if type(digest) is not str:
        raise ValueError("digest must be a string")
    return digest


def _blocked_reason_codes(values: Mapping[str, bool]) -> tuple[str, ...]:
    return tuple(
        reason
        for field_name, reason in BLOCKED_REASON_BY_FIELD.items()
        if values[field_name] is not True
    )


def _attention_reason_codes(values: Mapping[str, bool]) -> tuple[str, ...]:
    reasons: list[str] = []
    if values["operator_safety_digest_present"] is not True:
        reasons.append(OPERATOR_SAFETY_ATTENTION_REASON)
    if any(values[field_name] is not True for field_name in ARTIFACT_FIELDS):
        reasons.append(INCOMPLETE_ATTENTION_REASON)
    return tuple(reasons)


def _validate_report(report: ProbabilityEventScreenReviewPacketIndexReport) -> None:
    artifact_values = {
        field_name: getattr(report, field_name) for field_name in ARTIFACT_FIELDS
    }
    present_count = _count(sum(1 for value in artifact_values.values() if value is True))
    missing_count = _count(
        sum(1 for value in artifact_values.values() if value is not True),
    )
    completeness_score = _ratio(present_count, ARTIFACT_COUNT)
    blocked_reason_codes = _blocked_reason_codes(artifact_values)
    if not blocked_reason_codes:
        blocked_reason_codes = (READY_REASON,)
    attention_reason_codes = _attention_reason_codes(artifact_values)
    if report.artifact_count != ARTIFACT_COUNT:
        raise ValueError("artifact_count must match the review packet artifact list")
    if report.present_artifact_count != present_count:
        raise ValueError("present_artifact_count must match artifact flags")
    if report.missing_artifact_count != missing_count:
        raise ValueError("missing_artifact_count must match artifact flags")
    if report.index_completeness_score != completeness_score:
        raise ValueError("index_completeness_score must match artifact flags")
    if report.ready_ratio != completeness_score:
        raise ValueError("ready_ratio must match artifact flags")
    if report.blocked_reason_codes != blocked_reason_codes:
        raise ValueError("blocked_reason_codes must match artifact flags")
    if report.attention_reason_codes != attention_reason_codes:
        raise ValueError("attention_reason_codes must match artifact flags")
    if report.review_packet_index_ready != (blocked_reason_codes == (READY_REASON,)):
        raise ValueError("review_packet_index_ready must match artifact flags")


def _validate_public_payload(
    payload: Mapping[str, object],
) -> None:
    if set(payload) != set(PAYLOAD_KEYS):
        raise ValueError("public payload fields must match the report schema exactly")
    for field_name in ARTIFACT_FIELDS:
        _require_bool(field_name, payload[field_name])
    _require_bool("review_packet_index_ready", payload["review_packet_index_ready"])
    _require_public_label("config_version", payload["config_version"])
    _require_decimal_string("artifact_count", payload["artifact_count"])
    _require_decimal_string("present_artifact_count", payload["present_artifact_count"])
    _require_decimal_string("missing_artifact_count", payload["missing_artifact_count"])
    _require_decimal_string(
        "index_completeness_score",
        payload["index_completeness_score"],
    )
    _require_decimal_string("ready_ratio", payload["ready_ratio"])
    _normalize_blocked_reason_codes(_require_string_tuple(payload["blocked_reason_codes"]))
    _normalize_attention_reason_codes(
        _require_string_tuple(payload["attention_reason_codes"]),
    )
    _require_public_label("digest", payload["digest"])
    _require_digest("digest", payload["digest"])
    _require_hard_flags(_MappingFlags(payload))
    expected_digest = _payload_digest(dict(payload) | {"digest": ""})
    if payload["digest"] != expected_digest:
        raise ValueError("digest must match public payload")


@dataclass(frozen=True)
class _MappingFlags:
    value: Mapping[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _payload_items(
    report: ProbabilityEventScreenReviewPacketIndexReport,
    *,
    digest: str,
) -> dict[str, object]:
    values = {
        "config_version": report.config_version,
        "review_packet_index_ready": report.review_packet_index_ready,
        **{field_name: getattr(report, field_name) for field_name in ARTIFACT_FIELDS},
        "artifact_count": report.artifact_count,
        "present_artifact_count": report.present_artifact_count,
        "missing_artifact_count": report.missing_artifact_count,
        "index_completeness_score": report.index_completeness_score,
        "blocked_reason_codes": report.blocked_reason_codes,
        "attention_reason_codes": report.attention_reason_codes,
        "ready_ratio": report.ready_ratio,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
        "digest": digest,
    }
    return _coerce_payload_values(values)


def _coerce_payload_values(values: Mapping[str, object]) -> dict[str, object]:
    payload: dict[str, object] = {}
    for key in PAYLOAD_KEYS:
        value = values[key]
        if type(value) is Decimal:
            payload[key] = format(value, "f")
        elif isinstance(value, tuple):
            payload[key] = value
        else:
            payload[key] = value
    return payload


def _payload_digest(payload: Mapping[str, object]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(canonical.encode("utf-8")).hexdigest()


def _require_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str or not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public label")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    return _quantize(value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return _quantize(value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value != value.to_integral_value() and value.as_tuple().exponent < -6:
        raise ValueError(f"{field_name} must use no more than six decimal places")
    return value


def _require_decimal_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal-derived string")
    parsed = Decimal(value)
    if format(_require_decimal(field_name, parsed), "f") != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return parsed


def _normalize_blocked_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    return _normalize_reason_codes(
        "blocked_reason_codes",
        values,
        allowed=BLOCKED_REASON_CODES,
    )


def _normalize_attention_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    return _normalize_reason_codes(
        "attention_reason_codes",
        values,
        allowed=ATTENTION_REASON_CODES,
    )


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
    *,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple or any(type(value) is not str for value in values):
        raise ValueError(f"{field_name} must be a tuple of reason code strings")
    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} must not contain duplicates")
    if any(value not in allowed for value in values):
        raise ValueError(f"{field_name} contains an unsupported reason code")
    return values


def _require_string_tuple(value: object) -> tuple[str, ...]:
    if type(value) is tuple and all(type(item) is str for item in value):
        return value
    if type(value) is list and all(type(item) is str for item in value):
        return tuple(value)
    raise ValueError("reason codes must be strings")


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)
