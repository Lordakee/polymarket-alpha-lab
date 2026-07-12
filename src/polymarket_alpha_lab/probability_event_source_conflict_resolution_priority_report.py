"""Paper-only source conflict priority report for probability events."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from re import Pattern, compile
from typing import Mapping


__all__ = (
    "PROBABILITY_EVENT_SOURCE_CONFLICT_RESOLUTION_PRIORITY_REPORT_VERSION",
    "PROBABILITY_EVENT_SOURCE_CONFLICT_RESOLUTION_PRIORITY_STATUSES",
    "ProbabilityEventSourceConflictResolutionPriorityInput",
    "ProbabilityEventSourceConflictResolutionPriorityReport",
    "build_probability_event_source_conflict_resolution_priority_report",
    "probability_event_source_conflict_resolution_priority_report_digest",
    "probability_event_source_conflict_resolution_priority_report_payload",
)


PROBABILITY_EVENT_SOURCE_CONFLICT_RESOLUTION_PRIORITY_REPORT_VERSION = (
    "probability-event-source-conflict-resolution-priority-v0"
)
PROBABILITY_EVENT_SOURCE_CONFLICT_RESOLUTION_PRIORITY_STATUSES = (
    "low",
    "high",
    "critical",
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")
THREE = Decimal("3.000000")
TWELVE = Decimal("12.000000")
TWENTY_FOUR = Decimal("24.000000")
MARKET_MOVE_WATCH = Decimal("0.050000")
DIGEST_RE: Pattern[str] = compile(r"^[0-9a-f]{64}$")

REASON_CODES = (
    "official_conflict_present",
    "source_conflict_cluster",
    "source_conflict_present",
    "source_freshness_gap_critical",
    "source_freshness_gap_watch",
    "market_move_watch",
    "manual_owner_missing",
    "manual_owner_assigned",
    "no_source_conflict_detected",
)
PAYLOAD_KEYS = (
    "config_version",
    "priority_status",
    "conflict_count",
    "official_conflict_count",
    "source_freshness_gap_hours",
    "market_move_probability",
    "manual_owner_assigned",
    "reason_codes",
    "manual_next_step",
    "paper_only",
    "report_only",
    "readonly",
    "payload_digest",
)


class ProbabilityEventSourceConflictResolutionPriorityPublicPayload(
    dict[str, object],
):
    """Immutable public payload for source conflict priority reports."""

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
class ProbabilityEventSourceConflictResolutionPriorityInput:
    conflict_count: Decimal
    official_conflict_count: Decimal
    source_freshness_gap_hours: Decimal
    market_move_probability: Decimal
    manual_owner_assigned: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventSourceConflictResolutionPriorityInput:
            raise TypeError(
                "ProbabilityEventSourceConflictResolutionPriorityInput "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventSourceConflictResolutionPriorityInput:
            raise ValueError(
                "input must be exactly "
                "ProbabilityEventSourceConflictResolutionPriorityInput",
            )
        object.__setattr__(
            self,
            "conflict_count",
            _require_count_decimal("conflict_count", self.conflict_count),
        )
        object.__setattr__(
            self,
            "official_conflict_count",
            _require_count_decimal(
                "official_conflict_count",
                self.official_conflict_count,
            ),
        )
        object.__setattr__(
            self,
            "source_freshness_gap_hours",
            _require_nonnegative_decimal(
                "source_freshness_gap_hours",
                self.source_freshness_gap_hours,
            ),
        )
        object.__setattr__(
            self,
            "market_move_probability",
            _require_ratio_decimal(
                "market_move_probability",
                self.market_move_probability,
            ),
        )
        _require_bool("manual_owner_assigned", self.manual_owner_assigned)
        _require_hard_flags(self)
        if self.official_conflict_count > self.conflict_count:
            raise ValueError("official_conflict_count must not exceed conflict_count")


@dataclass(frozen=True)
class ProbabilityEventSourceConflictResolutionPriorityReport:
    config_version: str
    priority_status: str
    conflict_count: Decimal
    official_conflict_count: Decimal
    source_freshness_gap_hours: Decimal
    market_move_probability: Decimal
    manual_owner_assigned: bool
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventSourceConflictResolutionPriorityReport:
            raise TypeError(
                "ProbabilityEventSourceConflictResolutionPriorityReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventSourceConflictResolutionPriorityReport:
            raise ValueError(
                "report must be exactly "
                "ProbabilityEventSourceConflictResolutionPriorityReport",
            )
        _require_config_version(self.config_version)
        _require_priority_status(self.priority_status)
        object.__setattr__(
            self,
            "conflict_count",
            _require_count_decimal("conflict_count", self.conflict_count),
        )
        object.__setattr__(
            self,
            "official_conflict_count",
            _require_count_decimal(
                "official_conflict_count",
                self.official_conflict_count,
            ),
        )
        object.__setattr__(
            self,
            "source_freshness_gap_hours",
            _require_nonnegative_decimal(
                "source_freshness_gap_hours",
                self.source_freshness_gap_hours,
            ),
        )
        object.__setattr__(
            self,
            "market_move_probability",
            _require_ratio_decimal(
                "market_move_probability",
                self.market_move_probability,
            ),
        )
        _require_bool("manual_owner_assigned", self.manual_owner_assigned)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_manual_next_step(self.manual_next_step)
        _require_digest("payload_digest", self.payload_digest)
        _require_hard_flags(self)
        _validate_report(self)
        expected_digest = _payload_digest(_payload_items(self, payload_digest=""))
        if self.payload_digest != expected_digest:
            raise ValueError("payload_digest must match public payload")

    @property
    def public_payload(
        self,
    ) -> ProbabilityEventSourceConflictResolutionPriorityPublicPayload:
        payload = ProbabilityEventSourceConflictResolutionPriorityPublicPayload(
            _payload_items(self, payload_digest=self.payload_digest),
        )
        _validate_public_payload(payload)
        return payload


def build_probability_event_source_conflict_resolution_priority_report(
    inputs: ProbabilityEventSourceConflictResolutionPriorityInput,
) -> ProbabilityEventSourceConflictResolutionPriorityReport:
    """Build a deterministic readonly priority report for source conflicts."""

    if type(inputs) is not ProbabilityEventSourceConflictResolutionPriorityInput:
        raise ValueError(
            "inputs must be a ProbabilityEventSourceConflictResolutionPriorityInput",
        )
    _require_hard_flags(inputs)
    reason_codes = _reason_codes(inputs)
    priority_status = _priority_status(inputs, reason_codes)
    manual_next_step = _manual_next_step(
        priority_status=priority_status,
        reason_codes=reason_codes,
        manual_owner_assigned=inputs.manual_owner_assigned,
    )
    values: dict[str, object] = {
        "config_version": (
            PROBABILITY_EVENT_SOURCE_CONFLICT_RESOLUTION_PRIORITY_REPORT_VERSION
        ),
        "priority_status": priority_status,
        "conflict_count": inputs.conflict_count,
        "official_conflict_count": inputs.official_conflict_count,
        "source_freshness_gap_hours": inputs.source_freshness_gap_hours,
        "market_move_probability": inputs.market_move_probability,
        "manual_owner_assigned": inputs.manual_owner_assigned,
        "reason_codes": reason_codes,
        "manual_next_step": manual_next_step,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ProbabilityEventSourceConflictResolutionPriorityReport(
        **values,
        payload_digest=_payload_digest(_payload_values(values, payload_digest="")),
    )


def probability_event_source_conflict_resolution_priority_report_payload(
    report: ProbabilityEventSourceConflictResolutionPriorityReport,
) -> ProbabilityEventSourceConflictResolutionPriorityPublicPayload:
    if type(report) is not ProbabilityEventSourceConflictResolutionPriorityReport:
        raise ValueError(
            "report must be a ProbabilityEventSourceConflictResolutionPriorityReport",
        )
    _require_hard_flags(report)
    _validate_report(report)
    expected_digest = probability_event_source_conflict_resolution_priority_report_digest(
        report,
    )
    if report.payload_digest != expected_digest:
        raise ValueError("payload_digest must match report payload")
    return report.public_payload


def probability_event_source_conflict_resolution_priority_report_digest(
    report: ProbabilityEventSourceConflictResolutionPriorityReport,
) -> str:
    if type(report) is not ProbabilityEventSourceConflictResolutionPriorityReport:
        raise ValueError(
            "report must be a ProbabilityEventSourceConflictResolutionPriorityReport",
        )
    _require_hard_flags(report)
    _validate_report(report)
    return _payload_digest(_payload_items(report, payload_digest=""))


def _reason_codes(
    inputs: ProbabilityEventSourceConflictResolutionPriorityInput,
) -> tuple[str, ...]:
    if inputs.conflict_count == ZERO:
        return ("no_source_conflict_detected",)
    reasons: list[str] = []
    if inputs.official_conflict_count > ZERO:
        reasons.append("official_conflict_present")
    if inputs.conflict_count >= THREE:
        reasons.append("source_conflict_cluster")
    elif inputs.conflict_count > ZERO:
        reasons.append("source_conflict_present")
    if inputs.source_freshness_gap_hours >= TWENTY_FOUR:
        reasons.append("source_freshness_gap_critical")
    elif inputs.source_freshness_gap_hours >= TWELVE:
        reasons.append("source_freshness_gap_watch")
    if inputs.market_move_probability >= MARKET_MOVE_WATCH:
        reasons.append("market_move_watch")
    if inputs.manual_owner_assigned:
        reasons.append("manual_owner_assigned")
    else:
        reasons.append("manual_owner_missing")
    return tuple(reasons)


def _priority_status(
    inputs: ProbabilityEventSourceConflictResolutionPriorityInput,
    reason_codes: tuple[str, ...],
) -> str:
    if "no_source_conflict_detected" in reason_codes:
        return "low"
    if (
        inputs.official_conflict_count > ZERO
        or "source_freshness_gap_critical" in reason_codes
        or "manual_owner_missing" in reason_codes
    ):
        return "critical"
    return "high"


def _manual_next_step(
    *,
    priority_status: str,
    reason_codes: tuple[str, ...],
    manual_owner_assigned: bool,
) -> str:
    if "no_source_conflict_detected" in reason_codes:
        return "continue_readonly_monitoring"
    if not manual_owner_assigned and "official_conflict_present" in reason_codes:
        return "assign_owner_for_official_conflict_reconciliation"
    if not manual_owner_assigned:
        return "assign_owner_for_source_reconciliation"
    if priority_status == "critical":
        return "owner_escalates_conflict_reconciliation_before_report_refresh"
    return "owner_prioritizes_source_reconciliation_before_report_refresh"


def _validate_report(
    report: ProbabilityEventSourceConflictResolutionPriorityReport,
) -> None:
    if report.official_conflict_count > report.conflict_count:
        raise ValueError("official_conflict_count must not exceed conflict_count")
    expected_input = ProbabilityEventSourceConflictResolutionPriorityInput(
        conflict_count=report.conflict_count,
        official_conflict_count=report.official_conflict_count,
        source_freshness_gap_hours=report.source_freshness_gap_hours,
        market_move_probability=report.market_move_probability,
        manual_owner_assigned=report.manual_owner_assigned,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    expected_reason_codes = _reason_codes(expected_input)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match report inputs")
    expected_priority_status = _priority_status(expected_input, expected_reason_codes)
    if report.priority_status != expected_priority_status:
        raise ValueError("priority_status must match reason codes")
    expected_manual_next_step = _manual_next_step(
        priority_status=expected_priority_status,
        reason_codes=expected_reason_codes,
        manual_owner_assigned=report.manual_owner_assigned,
    )
    if report.manual_next_step != expected_manual_next_step:
        raise ValueError("manual_next_step must match priority status")


def _validate_public_payload(payload: Mapping[str, object]) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    if tuple(payload.keys()) != PAYLOAD_KEYS:
        raise ValueError("payload must match the canonical priority report schema")
    _require_config_version(payload["config_version"])
    _require_priority_status(payload["priority_status"])
    for field_name in ("paper_only", "report_only", "readonly"):
        _require_bool(field_name, payload[field_name])
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    _require_bool("manual_owner_assigned", payload["manual_owner_assigned"])
    for field_name in (
        "conflict_count",
        "official_conflict_count",
        "source_freshness_gap_hours",
        "market_move_probability",
    ):
        value = payload[field_name]
        if type(value) is not str:
            raise ValueError(f"{field_name} must be serialized as a string")
        if field_name == "market_move_probability":
            _require_ratio_decimal(field_name, Decimal(value))
        elif field_name.endswith("_count"):
            _require_count_decimal(field_name, Decimal(value))
        else:
            _require_nonnegative_decimal(field_name, Decimal(value))
    reason_codes = payload["reason_codes"]
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    _normalize_reason_codes(reason_codes)
    if type(payload["manual_next_step"]) is not str:
        raise ValueError("manual_next_step must be a string")
    digest = payload["payload_digest"]
    _require_digest("payload_digest", digest)
    unsigned = dict(payload)
    unsigned["payload_digest"] = ""
    if digest != _payload_digest(unsigned):
        raise ValueError("payload_digest must match public payload")
    return payload


def _payload_items(
    report: ProbabilityEventSourceConflictResolutionPriorityReport,
    *,
    payload_digest: str,
) -> dict[str, object]:
    return _payload_values(_report_values_without_digest(report), payload_digest=payload_digest)


def _report_values_without_digest(
    report: ProbabilityEventSourceConflictResolutionPriorityReport,
) -> dict[str, object]:
    return {
        "config_version": report.config_version,
        "priority_status": report.priority_status,
        "conflict_count": report.conflict_count,
        "official_conflict_count": report.official_conflict_count,
        "source_freshness_gap_hours": report.source_freshness_gap_hours,
        "market_move_probability": report.market_move_probability,
        "manual_owner_assigned": report.manual_owner_assigned,
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
        "priority_status": values["priority_status"],
        "conflict_count": _decimal_text(values["conflict_count"]),
        "official_conflict_count": _decimal_text(values["official_conflict_count"]),
        "source_freshness_gap_hours": _decimal_text(
            values["source_freshness_gap_hours"],
        ),
        "market_move_probability": _decimal_text(values["market_move_probability"]),
        "manual_owner_assigned": values["manual_owner_assigned"],
        "reason_codes": values["reason_codes"],
        "manual_next_step": values["manual_next_step"],
        "paper_only": values["paper_only"],
        "report_only": values["report_only"],
        "readonly": values["readonly"],
        "payload_digest": payload_digest,
    }


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = getattr(value, field_name)
        if flag is not True:
            raise ValueError(f"{field_name} must be True")


def _require_config_version(value: object) -> None:
    if value != PROBABILITY_EVENT_SOURCE_CONFLICT_RESOLUTION_PRIORITY_REPORT_VERSION:
        raise ValueError("config_version must be the supported report version")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be exactly bool")


def _require_priority_status(value: object) -> None:
    if (
        type(value) is not str
        or value not in PROBABILITY_EVENT_SOURCE_CONFLICT_RESOLUTION_PRIORITY_STATUSES
    ):
        raise ValueError("priority_status must be supported")


def _require_manual_next_step(value: object) -> None:
    allowed = (
        "continue_readonly_monitoring",
        "assign_owner_for_official_conflict_reconciliation",
        "assign_owner_for_source_reconciliation",
        "owner_escalates_conflict_reconciliation_before_report_refresh",
        "owner_prioritizes_source_reconciliation_before_report_refresh",
    )
    if type(value) is not str or value not in allowed:
        raise ValueError("manual_next_step must be supported")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        if type(reason_code) is not str or reason_code not in REASON_CODES:
            raise ValueError("reason_codes must contain supported values")
    expected = tuple(reason_code for reason_code in REASON_CODES if reason_code in value)
    if value != expected:
        raise ValueError("reason_codes must be sorted and unique")
    if "no_source_conflict_detected" in value and len(value) != 1:
        raise ValueError("reason_codes clear state must be exclusive")
    if "manual_owner_missing" in value and "manual_owner_assigned" in value:
        raise ValueError("reason_codes owner state is mutually exclusive")
    return value


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _decimal_text(value: object) -> str:
    if type(value) is not Decimal:
        raise ValueError("payload Decimal fields must be Decimal")
    return format(value.quantize(QUANTUM, rounding=ROUND_HALF_UP), "f")


def _payload_digest(payload: Mapping[str, object]) -> str:
    return sha256(
        json.dumps(
            dict(payload),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()
