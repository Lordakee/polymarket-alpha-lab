"""Read-only outcome dependency collision report for probability events."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from re import Pattern, compile
from typing import Mapping


__all__ = (
    "PROBABILITY_EVENT_OUTCOME_DEPENDENCY_COLLISION_REPORT_VERSION",
    "ProbabilityEventOutcomeDependencyCollisionInput",
    "ProbabilityEventOutcomeDependencyCollisionReport",
    "build_probability_event_outcome_dependency_collision_report",
    "probability_event_outcome_dependency_collision_report_payload",
    "probability_event_outcome_dependency_collision_report_digest",
)


PROBABILITY_EVENT_OUTCOME_DEPENDENCY_COLLISION_REPORT_VERSION = (
    "probability-event-outcome-dependency-collision-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
DIGEST_RE: Pattern[str] = compile(r"^[0-9a-f]{64}$")

COLLISION_STATUSES = ("clear", "watch", "blocked")
NO_COLLISION_REASON = "no_dependency_collision_detected"
CONFLICT_AT_OR_ABOVE_THRESHOLD_REASON = (
    "conflicting_dependency_count_at_or_above_threshold"
)
CONFLICT_BELOW_THRESHOLD_REASON = "conflicting_dependency_count_below_threshold"
SHARED_WITHOUT_OFFICIAL_REASON = "shared_dependencies_without_official_dependency"
REASON_CODES = (
    NO_COLLISION_REASON,
    CONFLICT_AT_OR_ABOVE_THRESHOLD_REASON,
    CONFLICT_BELOW_THRESHOLD_REASON,
    SHARED_WITHOUT_OFFICIAL_REASON,
)
PAYLOAD_KEYS = (
    "config_version",
    "outcome_count",
    "shared_dependency_count",
    "conflicting_dependency_count",
    "official_dependency_count",
    "collision_threshold_count",
    "collision_status",
    "reason_codes",
    "manual_next_step",
    "paper_only",
    "report_only",
    "readonly",
    "payload_digest",
)


class ProbabilityEventOutcomeDependencyCollisionPublicPayload(dict[str, object]):
    """Immutable public payload for the outcome dependency collision report."""

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
class ProbabilityEventOutcomeDependencyCollisionInput:
    outcome_count: Decimal
    shared_dependency_count: Decimal
    conflicting_dependency_count: Decimal
    official_dependency_count: Decimal
    collision_threshold_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventOutcomeDependencyCollisionInput:
            raise TypeError(
                "ProbabilityEventOutcomeDependencyCollisionInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventOutcomeDependencyCollisionInput:
            raise ValueError(
                "input must be exactly ProbabilityEventOutcomeDependencyCollisionInput",
            )
        for field_name in (
            "outcome_count",
            "shared_dependency_count",
            "conflicting_dependency_count",
            "official_dependency_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "collision_threshold_count",
            _require_positive_count_decimal(
                "collision_threshold_count",
                self.collision_threshold_count,
            ),
        )
        _require_hard_flags(self)
        _validate_counts(self)


@dataclass(frozen=True)
class ProbabilityEventOutcomeDependencyCollisionReport:
    config_version: str
    outcome_count: Decimal
    shared_dependency_count: Decimal
    conflicting_dependency_count: Decimal
    official_dependency_count: Decimal
    collision_threshold_count: Decimal
    collision_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventOutcomeDependencyCollisionReport:
            raise TypeError(
                "ProbabilityEventOutcomeDependencyCollisionReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventOutcomeDependencyCollisionReport:
            raise ValueError(
                "report must be exactly ProbabilityEventOutcomeDependencyCollisionReport",
            )
        _require_config_version(self.config_version)
        for field_name in (
            "outcome_count",
            "shared_dependency_count",
            "conflicting_dependency_count",
            "official_dependency_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "collision_threshold_count",
            _require_positive_count_decimal(
                "collision_threshold_count",
                self.collision_threshold_count,
            ),
        )
        _require_collision_status(self.collision_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_manual_next_step(self.manual_next_step)
        _require_payload_digest("payload_digest", self.payload_digest)
        _require_hard_flags(self)
        _validate_counts(self)
        _validate_report(self)
        expected_digest = _payload_digest(_payload_items(self, payload_digest=""))
        if self.payload_digest != expected_digest:
            raise ValueError("payload_digest must match public payload")

    @property
    def public_payload(self) -> ProbabilityEventOutcomeDependencyCollisionPublicPayload:
        payload = ProbabilityEventOutcomeDependencyCollisionPublicPayload(
            _payload_items(self, payload_digest=self.payload_digest),
        )
        _validate_public_payload(payload)
        return payload


def build_probability_event_outcome_dependency_collision_report(
    inputs: ProbabilityEventOutcomeDependencyCollisionInput,
) -> ProbabilityEventOutcomeDependencyCollisionReport:
    """Build a deterministic paper-only outcome dependency collision report."""

    if type(inputs) is not ProbabilityEventOutcomeDependencyCollisionInput:
        raise ValueError(
            "inputs must be a ProbabilityEventOutcomeDependencyCollisionInput",
        )
    _require_hard_flags(inputs)
    _validate_counts(inputs)
    reason_codes = _reason_codes_for_counts(inputs)
    collision_status = _collision_status(reason_codes)
    manual_next_step = _manual_next_step(collision_status)
    values: dict[str, object] = {
        "config_version": PROBABILITY_EVENT_OUTCOME_DEPENDENCY_COLLISION_REPORT_VERSION,
        "outcome_count": inputs.outcome_count,
        "shared_dependency_count": inputs.shared_dependency_count,
        "conflicting_dependency_count": inputs.conflicting_dependency_count,
        "official_dependency_count": inputs.official_dependency_count,
        "collision_threshold_count": inputs.collision_threshold_count,
        "collision_status": collision_status,
        "reason_codes": reason_codes,
        "manual_next_step": manual_next_step,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ProbabilityEventOutcomeDependencyCollisionReport(
        **values,
        payload_digest=_payload_digest(_payload_values(values, payload_digest="")),
    )


def probability_event_outcome_dependency_collision_report_payload(
    report: ProbabilityEventOutcomeDependencyCollisionReport,
) -> ProbabilityEventOutcomeDependencyCollisionPublicPayload:
    if type(report) is not ProbabilityEventOutcomeDependencyCollisionReport:
        raise ValueError(
            "report must be a ProbabilityEventOutcomeDependencyCollisionReport",
        )
    _require_hard_flags(report)
    _validate_report(report)
    expected_digest = probability_event_outcome_dependency_collision_report_digest(report)
    if report.payload_digest != expected_digest:
        raise ValueError("payload_digest must match report payload")
    return report.public_payload


def probability_event_outcome_dependency_collision_report_digest(
    report: ProbabilityEventOutcomeDependencyCollisionReport,
) -> str:
    if type(report) is not ProbabilityEventOutcomeDependencyCollisionReport:
        raise ValueError(
            "report must be a ProbabilityEventOutcomeDependencyCollisionReport",
        )
    _require_hard_flags(report)
    _validate_report(report)
    return _payload_digest(_payload_items(report, payload_digest=""))


def _validate_report(
    report: ProbabilityEventOutcomeDependencyCollisionReport,
) -> None:
    reason_codes = _reason_codes_for_counts(report)
    collision_status = _collision_status(reason_codes)
    if report.reason_codes != reason_codes:
        raise ValueError("reason_codes must match dependency collision counts")
    if report.collision_status != collision_status:
        raise ValueError("collision_status must match reason codes")
    if report.manual_next_step != _manual_next_step(collision_status):
        raise ValueError("manual_next_step must match collision_status")


def _validate_public_payload(
    payload: Mapping[str, object],
) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    if tuple(payload.keys()) != PAYLOAD_KEYS:
        raise ValueError("payload must match the canonical collision report schema")
    _require_config_version(payload["config_version"])
    for field_name in (
        "outcome_count",
        "shared_dependency_count",
        "conflicting_dependency_count",
        "official_dependency_count",
        "collision_threshold_count",
    ):
        value = payload[field_name]
        if type(value) is not str:
            raise ValueError(f"{field_name} must be serialized as a string")
        if field_name == "collision_threshold_count":
            _require_positive_count_decimal(field_name, Decimal(value))
        else:
            _require_count_decimal(field_name, Decimal(value))
    _require_collision_status(payload["collision_status"])
    _normalize_reason_codes(payload["reason_codes"])
    _require_manual_next_step(payload["manual_next_step"])
    for flag_name in ("paper_only", "report_only", "readonly"):
        if payload[flag_name] is not True:
            raise ValueError(f"{flag_name} must be True")
    payload_digest = payload["payload_digest"]
    _require_payload_digest("payload_digest", payload_digest)
    unsigned = dict(payload)
    unsigned["payload_digest"] = ""
    if payload_digest != _payload_digest(unsigned):
        raise ValueError("payload_digest must match public payload")
    return payload


def _payload_items(
    report: ProbabilityEventOutcomeDependencyCollisionReport,
    *,
    payload_digest: str,
) -> dict[str, object]:
    return _payload_values(_report_values_without_digest(report), payload_digest=payload_digest)


def _report_values_without_digest(
    report: ProbabilityEventOutcomeDependencyCollisionReport,
) -> dict[str, object]:
    return {
        "config_version": report.config_version,
        "outcome_count": report.outcome_count,
        "shared_dependency_count": report.shared_dependency_count,
        "conflicting_dependency_count": report.conflicting_dependency_count,
        "official_dependency_count": report.official_dependency_count,
        "collision_threshold_count": report.collision_threshold_count,
        "collision_status": report.collision_status,
        "reason_codes": report.reason_codes,
        "manual_next_step": report.manual_next_step,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _payload_values(
    values: Mapping[str, object],
    *,
    payload_digest: str,
) -> dict[str, object]:
    return {
        "config_version": values["config_version"],
        "outcome_count": _decimal_text(values["outcome_count"]),
        "shared_dependency_count": _decimal_text(values["shared_dependency_count"]),
        "conflicting_dependency_count": _decimal_text(
            values["conflicting_dependency_count"],
        ),
        "official_dependency_count": _decimal_text(values["official_dependency_count"]),
        "collision_threshold_count": _decimal_text(values["collision_threshold_count"]),
        "collision_status": values["collision_status"],
        "reason_codes": values["reason_codes"],
        "manual_next_step": values["manual_next_step"],
        "paper_only": values["paper_only"],
        "report_only": values["report_only"],
        "readonly": values["readonly"],
        "payload_digest": payload_digest,
    }


def _reason_codes_for_counts(value: object) -> tuple[str, ...]:
    shared_dependency_count = getattr(value, "shared_dependency_count")
    conflicting_dependency_count = getattr(value, "conflicting_dependency_count")
    official_dependency_count = getattr(value, "official_dependency_count")
    collision_threshold_count = getattr(value, "collision_threshold_count")
    reasons: list[str] = []
    if conflicting_dependency_count >= collision_threshold_count:
        reasons.append(CONFLICT_AT_OR_ABOVE_THRESHOLD_REASON)
    elif conflicting_dependency_count > ZERO:
        reasons.append(CONFLICT_BELOW_THRESHOLD_REASON)
    if shared_dependency_count > ZERO and official_dependency_count == ZERO:
        reasons.append(SHARED_WITHOUT_OFFICIAL_REASON)
    if not reasons:
        reasons.append(NO_COLLISION_REASON)
    return tuple(reasons)


def _collision_status(reason_codes: tuple[str, ...]) -> str:
    if CONFLICT_AT_OR_ABOVE_THRESHOLD_REASON in reason_codes:
        return "blocked"
    if reason_codes != (NO_COLLISION_REASON,):
        return "watch"
    return "clear"


def _manual_next_step(collision_status: str) -> str:
    if collision_status == "blocked":
        return (
            "Pause any automated action path and complete manual outcome dependency review."
        )
    if collision_status == "watch":
        return "Manually review outcome dependency mapping before escalating this event."
    return "Continue read-only monitoring; no manual collision review is required."


def _validate_counts(value: object) -> None:
    outcome_count = getattr(value, "outcome_count")
    shared_dependency_count = getattr(value, "shared_dependency_count")
    conflicting_dependency_count = getattr(value, "conflicting_dependency_count")
    official_dependency_count = getattr(value, "official_dependency_count")
    if shared_dependency_count > outcome_count:
        raise ValueError("shared_dependency_count cannot exceed outcome_count")
    if conflicting_dependency_count > shared_dependency_count:
        raise ValueError(
            "conflicting_dependency_count cannot exceed shared_dependency_count",
        )
    if official_dependency_count > shared_dependency_count:
        raise ValueError("official_dependency_count cannot exceed shared_dependency_count")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not value:
        raise ValueError("reason_codes must not be empty")
    if len(set(value)) != len(value):
        raise ValueError("reason_codes must be unique")
    for reason_code in value:
        if type(reason_code) is not str or reason_code not in REASON_CODES:
            raise ValueError("reason_code must be supported")
    if NO_COLLISION_REASON in value and value != (NO_COLLISION_REASON,):
        raise ValueError("no collision reason cannot be combined")
    return value


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = getattr(value, field_name)
        if flag is not True:
            raise ValueError(f"{field_name} must be True")


def _require_config_version(value: object) -> None:
    if value != PROBABILITY_EVENT_OUTCOME_DEPENDENCY_COLLISION_REPORT_VERSION:
        raise ValueError("config_version must be the supported report version")


def _require_collision_status(value: object) -> None:
    if type(value) is not str or value not in COLLISION_STATUSES:
        raise ValueError("collision_status must be supported")


def _require_manual_next_step(value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError("manual_next_step must be a non-empty string")


def _require_payload_digest(field_name: str, value: object) -> None:
    if type(value) is not str or DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


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
