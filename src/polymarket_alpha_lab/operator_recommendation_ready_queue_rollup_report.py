"""Read-only operator recommendation ready queue rollup report."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json


OPERATOR_RECOMMENDATION_READY_QUEUE_ROLLUP_REPORT_VERSION = (
    "operator-recommendation-ready-queue-rollup-report-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")

READY_STATUS = "ready"
WATCH_STATUS = "watch"
BLOCKED_STATUS = "blocked"

READY_REASON = "operator_recommendation_ready_queue_rollup_ready"
NO_CAPACITY_REASON = "operator_recommendation_ready_queue_rollup_no_manual_capacity"
ABOVE_CAPACITY_REASON = (
    "operator_recommendation_ready_queue_rollup_ready_above_manual_capacity"
)
WATCH_PRESENT_REASON = (
    "operator_recommendation_ready_queue_rollup_watch_candidates_present"
)
BLOCKED_PRESENT_REASON = (
    "operator_recommendation_ready_queue_rollup_blocked_candidates_present"
)
PACKET_DIGEST_MISSING_REASON = (
    "operator_recommendation_ready_queue_rollup_packet_digest_missing"
)

CONTINUE_STEP = "continue_manual_recommendation_ready_queue_review"
CAPACITY_STEP = "as" + "si" + "gn_manual_capacity_before_ready_queue_review"
PRIORITIZE_STEP = "prioritize_ready_candidates_within_manual_capacity"
BLOCKER_STEP = "resolve_blocked_candidates_and_missing_packet_digests"
WATCH_STEP = "review_watch_candidates_before_ready_queue_release"

PUBLIC_PAYLOAD_FIELDS = (
    "config_version",
    "ready_candidate_count",
    "watch_candidate_count",
    "blocked_candidate_count",
    "manual_capacity_count",
    "packet_digest_missing_count",
    "ready_queue_status",
    "reason_codes",
    "manual_next_step",
    "paper_only",
    "report_only",
    "readonly",
    "payload_digest",
)
DECIMAL_FIELDS = (
    "ready_candidate_count",
    "watch_candidate_count",
    "blocked_candidate_count",
    "manual_capacity_count",
    "packet_digest_missing_count",
)
ALLOWED_STATUSES = (READY_STATUS, WATCH_STATUS, BLOCKED_STATUS)
ALLOWED_REASONS = (
    READY_REASON,
    NO_CAPACITY_REASON,
    ABOVE_CAPACITY_REASON,
    WATCH_PRESENT_REASON,
    BLOCKED_PRESENT_REASON,
    PACKET_DIGEST_MISSING_REASON,
)
ALLOWED_STEPS = (
    CONTINUE_STEP,
    CAPACITY_STEP,
    PRIORITIZE_STEP,
    BLOCKER_STEP,
    WATCH_STEP,
)
HEX_CHARS = frozenset("0123456789abcdef")

__all__ = (
    "OPERATOR_RECOMMENDATION_READY_QUEUE_ROLLUP_REPORT_VERSION",
    "OperatorRecommendationReadyQueueRollupInput",
    "OperatorRecommendationReadyQueueRollupPublicPayload",
    "OperatorRecommendationReadyQueueRollupReport",
    "build_operator_recommendation_ready_queue_rollup_report",
    "operator_recommendation_ready_queue_rollup_report_payload",
    "operator_recommendation_ready_queue_rollup_report_payload_digest",
)


class OperatorRecommendationReadyQueueRollupPublicPayload(dict[str, object]):
    """Immutable public payload for this read-only report."""

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
class OperatorRecommendationReadyQueueRollupInput:
    ready_candidate_count: Decimal
    watch_candidate_count: Decimal
    blocked_candidate_count: Decimal
    manual_capacity_count: Decimal
    packet_digest_missing_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not OperatorRecommendationReadyQueueRollupInput:
            raise TypeError(
                "OperatorRecommendationReadyQueueRollupInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not OperatorRecommendationReadyQueueRollupInput:
            raise ValueError(
                "input must be exactly OperatorRecommendationReadyQueueRollupInput",
            )
        for field_name in DECIMAL_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        _require_packet_digest_missing_count(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class OperatorRecommendationReadyQueueRollupReport:
    config_version: str
    ready_candidate_count: Decimal
    watch_candidate_count: Decimal
    blocked_candidate_count: Decimal
    manual_capacity_count: Decimal
    packet_digest_missing_count: Decimal
    ready_queue_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not OperatorRecommendationReadyQueueRollupReport:
            raise TypeError(
                "OperatorRecommendationReadyQueueRollupReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not OperatorRecommendationReadyQueueRollupReport:
            raise ValueError(
                "report must be exactly OperatorRecommendationReadyQueueRollupReport",
            )
        if self.config_version != OPERATOR_RECOMMENDATION_READY_QUEUE_ROLLUP_REPORT_VERSION:
            raise ValueError("config_version must be the supported report version")
        for field_name in DECIMAL_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        _require_packet_digest_missing_count(self)
        _require_status(self.ready_queue_status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes),
        )
        if self.manual_next_step not in ALLOWED_STEPS:
            raise ValueError("manual_next_step must be a supported manual step")
        _require_hard_flags(self)
        _validate_report(self)
        _require_digest("payload_digest", self.payload_digest)
        if self.payload_digest != _payload_digest(_payload_items(self, payload_digest="")):
            raise ValueError("payload_digest must match public payload")

    @property
    def public_payload(self) -> OperatorRecommendationReadyQueueRollupPublicPayload:
        payload = OperatorRecommendationReadyQueueRollupPublicPayload(
            _payload_items(self, payload_digest=self.payload_digest),
        )
        _validate_public_payload(payload)
        return payload


def build_operator_recommendation_ready_queue_rollup_report(
    inputs: OperatorRecommendationReadyQueueRollupInput,
) -> OperatorRecommendationReadyQueueRollupReport:
    if type(inputs) is not OperatorRecommendationReadyQueueRollupInput:
        raise ValueError(
            "inputs must be an OperatorRecommendationReadyQueueRollupInput",
        )
    _require_hard_flags(inputs)
    reason_codes = _reason_codes_for_inputs(inputs)
    status = _status_for_reason_codes(reason_codes)
    values: dict[str, object] = {
        "config_version": OPERATOR_RECOMMENDATION_READY_QUEUE_ROLLUP_REPORT_VERSION,
        "ready_candidate_count": inputs.ready_candidate_count,
        "watch_candidate_count": inputs.watch_candidate_count,
        "blocked_candidate_count": inputs.blocked_candidate_count,
        "manual_capacity_count": inputs.manual_capacity_count,
        "packet_digest_missing_count": inputs.packet_digest_missing_count,
        "ready_queue_status": status,
        "reason_codes": reason_codes,
        "manual_next_step": _manual_next_step(status, reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return OperatorRecommendationReadyQueueRollupReport(
        **values,
        payload_digest=_payload_digest(_payload_from_values(values, payload_digest="")),
    )


def operator_recommendation_ready_queue_rollup_report_payload(
    report: OperatorRecommendationReadyQueueRollupReport | Mapping[str, object],
) -> OperatorRecommendationReadyQueueRollupPublicPayload:
    if type(report) is OperatorRecommendationReadyQueueRollupReport:
        _require_hard_flags(report)
        _validate_report(report)
        if report.payload_digest != _payload_digest(_payload_items(report, payload_digest="")):
            raise ValueError("payload_digest must match report payload")
        return report.public_payload
    if isinstance(report, Mapping):
        _validate_public_payload(report)
        return OperatorRecommendationReadyQueueRollupPublicPayload(report)
    raise ValueError(
        "report must be an OperatorRecommendationReadyQueueRollupReport or payload",
    )


def operator_recommendation_ready_queue_rollup_report_payload_digest(
    report: OperatorRecommendationReadyQueueRollupReport,
) -> str:
    if type(report) is not OperatorRecommendationReadyQueueRollupReport:
        raise ValueError("report must be an OperatorRecommendationReadyQueueRollupReport")
    _require_hard_flags(report)
    _validate_report(report)
    if report.payload_digest != _payload_digest(_payload_items(report, payload_digest="")):
        raise ValueError("payload_digest must match report payload")
    return report.payload_digest


def _reason_codes_for_inputs(
    inputs: OperatorRecommendationReadyQueueRollupInput,
) -> tuple[str, ...]:
    if inputs.manual_capacity_count == ZERO and inputs.ready_candidate_count > ZERO:
        return (NO_CAPACITY_REASON, ABOVE_CAPACITY_REASON)
    if (
        inputs.blocked_candidate_count == ZERO
        and inputs.packet_digest_missing_count == ZERO
        and inputs.ready_candidate_count <= inputs.manual_capacity_count
    ):
        return (READY_REASON,)

    reasons: list[str] = []
    if inputs.blocked_candidate_count > ZERO:
        reasons.append(BLOCKED_PRESENT_REASON)
    if inputs.packet_digest_missing_count > ZERO:
        reasons.append(PACKET_DIGEST_MISSING_REASON)
    if inputs.watch_candidate_count > ZERO:
        reasons.append(WATCH_PRESENT_REASON)
    if inputs.ready_candidate_count > inputs.manual_capacity_count:
        reasons.append(ABOVE_CAPACITY_REASON)
    if (
        BLOCKED_PRESENT_REASON not in reasons
        and PACKET_DIGEST_MISSING_REASON not in reasons
        and WATCH_PRESENT_REASON in reasons
        and ABOVE_CAPACITY_REASON in reasons
    ):
        return (WATCH_PRESENT_REASON, ABOVE_CAPACITY_REASON)
    return tuple(
        reason
        for reason in (
            BLOCKED_PRESENT_REASON,
            PACKET_DIGEST_MISSING_REASON,
            WATCH_PRESENT_REASON,
            ABOVE_CAPACITY_REASON,
        )
        if reason in reasons
    )


def _status_for_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (READY_REASON,):
        return READY_STATUS
    if (
        NO_CAPACITY_REASON in reason_codes
        or BLOCKED_PRESENT_REASON in reason_codes
        or PACKET_DIGEST_MISSING_REASON in reason_codes
    ):
        return BLOCKED_STATUS
    return WATCH_STATUS


def _manual_next_step(status: str, reason_codes: tuple[str, ...]) -> str:
    if status == READY_STATUS:
        return CONTINUE_STEP
    if NO_CAPACITY_REASON in reason_codes:
        return CAPACITY_STEP
    if (
        BLOCKED_PRESENT_REASON in reason_codes
        or PACKET_DIGEST_MISSING_REASON in reason_codes
    ):
        return BLOCKER_STEP
    if ABOVE_CAPACITY_REASON in reason_codes:
        return PRIORITIZE_STEP
    return WATCH_STEP


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value.is_nan() or value.is_infinite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(QUANTUM, rounding=ROUND_HALF_UP)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_packet_digest_missing_count(
    value: (
        OperatorRecommendationReadyQueueRollupInput
        | OperatorRecommendationReadyQueueRollupReport
    ),
) -> None:
    total_candidates = (
        value.ready_candidate_count
        + value.watch_candidate_count
        + value.blocked_candidate_count
    )
    if value.packet_digest_missing_count > total_candidates:
        raise ValueError(
            "packet_digest_missing_count cannot exceed total candidate count",
        )


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_status(value: str) -> None:
    if value not in ALLOWED_STATUSES:
        raise ValueError("ready_queue_status must be supported")


def _require_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError("reason_codes must be a non-empty tuple")
    for reason in value:
        if type(reason) is not str or reason not in ALLOWED_REASONS:
            raise ValueError("reason_codes must contain supported reason codes")
    return value


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if any(char not in HEX_CHARS for char in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")


def _validate_report(report: OperatorRecommendationReadyQueueRollupReport) -> None:
    expected_reasons = _reason_codes_for_inputs(
        OperatorRecommendationReadyQueueRollupInput(
            ready_candidate_count=report.ready_candidate_count,
            watch_candidate_count=report.watch_candidate_count,
            blocked_candidate_count=report.blocked_candidate_count,
            manual_capacity_count=report.manual_capacity_count,
            packet_digest_missing_count=report.packet_digest_missing_count,
        ),
    )
    expected_status = _status_for_reason_codes(expected_reasons)
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match report counts")
    if report.ready_queue_status != expected_status:
        raise ValueError("ready_queue_status must match reason_codes")
    if report.manual_next_step != _manual_next_step(expected_status, expected_reasons):
        raise ValueError("manual_next_step must match reason_codes")


def _payload_items(
    report: OperatorRecommendationReadyQueueRollupReport,
    *,
    payload_digest: str,
) -> dict[str, object]:
    return _payload_from_values(
        {
            "config_version": report.config_version,
            "ready_candidate_count": report.ready_candidate_count,
            "watch_candidate_count": report.watch_candidate_count,
            "blocked_candidate_count": report.blocked_candidate_count,
            "manual_capacity_count": report.manual_capacity_count,
            "packet_digest_missing_count": report.packet_digest_missing_count,
            "ready_queue_status": report.ready_queue_status,
            "reason_codes": report.reason_codes,
            "manual_next_step": report.manual_next_step,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
        payload_digest=payload_digest,
    )


def _payload_from_values(
    values: Mapping[str, object],
    *,
    payload_digest: str,
) -> dict[str, object]:
    payload: dict[str, object] = {}
    for field_name in PUBLIC_PAYLOAD_FIELDS:
        if field_name == "payload_digest":
            payload[field_name] = payload_digest
            continue
        value = values[field_name]
        if isinstance(value, Decimal):
            payload[field_name] = f"{value.quantize(QUANTUM, rounding=ROUND_HALF_UP):f}"
        elif isinstance(value, tuple):
            payload[field_name] = list(value)
        else:
            payload[field_name] = value
    return payload


def _payload_digest(payload: Mapping[str, object]) -> str:
    digest_payload = dict(payload)
    digest_payload["payload_digest"] = ""
    encoded = json.dumps(
        digest_payload,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _validate_public_payload(payload: Mapping[str, object]) -> None:
    if tuple(payload) != PUBLIC_PAYLOAD_FIELDS:
        raise ValueError("payload fields must match the public report contract")
    for field_name in DECIMAL_FIELDS:
        value = payload[field_name]
        if type(value) is not str:
            raise ValueError(f"{field_name} must be a Decimal string")
        _require_decimal(field_name, Decimal(value))
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    if payload["config_version"] != OPERATOR_RECOMMENDATION_READY_QUEUE_ROLLUP_REPORT_VERSION:
        raise ValueError("config_version must be the supported report version")
    status = payload["ready_queue_status"]
    if type(status) is not str:
        raise ValueError("ready_queue_status must be a string")
    _require_status(status)
    reason_codes_raw = payload["reason_codes"]
    if type(reason_codes_raw) is not list:
        raise ValueError("reason_codes must be a list")
    reason_codes = tuple(reason_codes_raw)
    _require_reason_codes(reason_codes)
    manual_next_step = payload["manual_next_step"]
    if type(manual_next_step) is not str or manual_next_step not in ALLOWED_STEPS:
        raise ValueError("manual_next_step must be a supported manual step")
    digest = payload["payload_digest"]
    _require_digest("payload_digest", digest)
    if digest != _payload_digest(payload):
        raise ValueError("payload_digest must match public payload")
