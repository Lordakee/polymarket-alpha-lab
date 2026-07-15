"""Read-only Phase 1 report for market resolution ambiguity escalation."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any, Mapping

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_MARKET_RESOLUTION_AMBIGUITY_ESCALATION_VERSION = (
    "market-resolution-ambiguity-escalation-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_LOW_CLARITY = Decimal("0.500000")
_PARTIAL_CLARITY = Decimal("0.800000")
_IMMINENT_RESOLUTION_HOURS = Decimal("24.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

AMBIGUITY_STATUSES = ("clear", "manual_review", "escalate")
READY_REASON_CODE = "resolution_rules_clear"
REASON_CODE_SEQUENCE = (
    "resolution_rule_clarity_low",
    "resolution_rule_clarity_partial",
    "oracle_dependency_present",
    "ambiguous_resolution_terms_present",
    "conflicting_resolution_sources_present",
    "resolution_window_imminent",
    READY_REASON_CODE,
)
MANUAL_NEXT_STEPS = (
    "continue_readonly_monitoring",
    "queue_manual_resolution_review",
    "escalate_to_manual_resolution_review",
)
PAYLOAD_KEYS = (
    "config_version",
    "resolution_rule_clarity",
    "oracle_dependency_count",
    "ambiguous_terms_count",
    "source_conflict_count",
    "time_to_resolution_hours",
    "ambiguity_status",
    "reason_codes",
    "manual_next_step",
    "paper_only",
    "report_only",
    "readonly",
    "payload_digest",
)
_UNSAFE_PUBLIC_FRAGMENTS = (
    "live",
    "auth",
    "wallet",
    "order",
    "key",
    "signature",
    "signing",
    "execution",
    "execute",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class MarketResolutionAmbiguityEscalationInput(_FinalDataclass):
    resolution_rule_clarity: Decimal
    oracle_dependency_count: Decimal
    ambiguous_terms_count: Decimal
    source_conflict_count: Decimal
    time_to_resolution_hours: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResolutionAmbiguityEscalationInput, "input")
        object.__setattr__(
            self,
            "resolution_rule_clarity",
            _require_ratio_decimal(
                "resolution_rule_clarity",
                self.resolution_rule_clarity,
            ),
        )
        for field_name in (
            "oracle_dependency_count",
            "ambiguous_terms_count",
            "source_conflict_count",
            "time_to_resolution_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags(
            "market resolution ambiguity escalation input",
            self,
        )


@dataclass(frozen=True)
class MarketResolutionAmbiguityEscalationReport(_FinalDataclass):
    config_version: str
    resolution_rule_clarity: Decimal
    oracle_dependency_count: Decimal
    ambiguous_terms_count: Decimal
    source_conflict_count: Decimal
    time_to_resolution_hours: Decimal
    ambiguity_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResolutionAmbiguityEscalationReport, "report")
        _require_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "resolution_rule_clarity",
            _require_ratio_decimal(
                "resolution_rule_clarity",
                self.resolution_rule_clarity,
            ),
        )
        for field_name in (
            "oracle_dependency_count",
            "ambiguous_terms_count",
            "source_conflict_count",
            "time_to_resolution_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "ambiguity_status",
            _require_member("ambiguity_status", self.ambiguity_status, AMBIGUITY_STATUSES),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "manual_next_step",
            _require_member("manual_next_step", self.manual_next_step, MANUAL_NEXT_STEPS),
        )
        _require_sha256("payload_digest", self.payload_digest)
        require_paper_only_flags(
            "market resolution ambiguity escalation report",
            self,
        )
        _validate_report(self)
        if self.payload_digest != _digest_from_payload(_payload_without_digest(self)):
            raise ValueError("payload_digest does not match report payload")

    @property
    def public_payload(self) -> dict[str, object]:
        return market_resolution_ambiguity_escalation_payload(self)


def build_market_resolution_ambiguity_escalation_report(
    ambiguity_input: MarketResolutionAmbiguityEscalationInput,
    *,
    config_version: str = DEFAULT_MARKET_RESOLUTION_AMBIGUITY_ESCALATION_VERSION,
) -> MarketResolutionAmbiguityEscalationReport:
    if type(ambiguity_input) is not MarketResolutionAmbiguityEscalationInput:
        raise ValueError(
            "ambiguity_input must be a MarketResolutionAmbiguityEscalationInput",
        )
    _require_public_string("config_version", config_version)
    require_paper_only_flags(
        "market resolution ambiguity escalation input",
        ambiguity_input,
    )

    reason_codes = _reason_codes_for_input(ambiguity_input)
    ambiguity_status = _status_for_reason_codes(reason_codes)
    manual_next_step = _manual_next_step_for_status(ambiguity_status)
    values: dict[str, object] = {
        "config_version": config_version,
        "resolution_rule_clarity": ambiguity_input.resolution_rule_clarity,
        "oracle_dependency_count": ambiguity_input.oracle_dependency_count,
        "ambiguous_terms_count": ambiguity_input.ambiguous_terms_count,
        "source_conflict_count": ambiguity_input.source_conflict_count,
        "time_to_resolution_hours": ambiguity_input.time_to_resolution_hours,
        "ambiguity_status": ambiguity_status,
        "reason_codes": reason_codes,
        "manual_next_step": manual_next_step,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return MarketResolutionAmbiguityEscalationReport(
        **values,
        payload_digest=_digest_from_payload(_json_payload(values)),
    )


def market_resolution_ambiguity_escalation_payload(
    report: MarketResolutionAmbiguityEscalationReport,
) -> dict[str, object]:
    if type(report) is not MarketResolutionAmbiguityEscalationReport:
        raise ValueError("report must be a MarketResolutionAmbiguityEscalationReport")
    require_paper_only_flags(
        "market resolution ambiguity escalation report",
        report,
    )
    _validate_report(report)
    payload_without_digest = _payload_without_digest(report)
    if report.payload_digest != _digest_from_payload(payload_without_digest):
        raise ValueError("payload_digest does not match report payload")
    payload = dict(payload_without_digest)
    payload["payload_digest"] = report.payload_digest
    validate_market_resolution_ambiguity_escalation_payload(payload)
    return payload


def market_resolution_ambiguity_escalation_payload_digest(
    report: MarketResolutionAmbiguityEscalationReport,
) -> str:
    if type(report) is not MarketResolutionAmbiguityEscalationReport:
        raise ValueError("report must be a MarketResolutionAmbiguityEscalationReport")
    payload = _payload_without_digest(report)
    payload_with_digest = dict(payload)
    payload_with_digest["payload_digest"] = _digest_from_payload(payload)
    validate_market_resolution_ambiguity_escalation_payload(payload_with_digest)
    return _digest_from_payload(payload)


def validate_market_resolution_ambiguity_escalation_payload(
    payload: Mapping[str, object],
) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    if tuple(payload.keys()) != PAYLOAD_KEYS:
        raise ValueError("payload must match the canonical ambiguity escalation schema")
    _reject_unsafe_public_values(payload)
    _require_public_string("config_version", payload["config_version"])
    resolution_rule_clarity = _payload_decimal(
        "resolution_rule_clarity",
        payload["resolution_rule_clarity"],
    )
    oracle_dependency_count = _payload_decimal(
        "oracle_dependency_count",
        payload["oracle_dependency_count"],
    )
    ambiguous_terms_count = _payload_decimal(
        "ambiguous_terms_count",
        payload["ambiguous_terms_count"],
    )
    source_conflict_count = _payload_decimal(
        "source_conflict_count",
        payload["source_conflict_count"],
    )
    time_to_resolution_hours = _payload_decimal(
        "time_to_resolution_hours",
        payload["time_to_resolution_hours"],
    )
    source = MarketResolutionAmbiguityEscalationInput(
        resolution_rule_clarity=resolution_rule_clarity,
        oracle_dependency_count=oracle_dependency_count,
        ambiguous_terms_count=ambiguous_terms_count,
        source_conflict_count=source_conflict_count,
        time_to_resolution_hours=time_to_resolution_hours,
        paper_only=payload["paper_only"],  # type: ignore[arg-type]
        report_only=payload["report_only"],  # type: ignore[arg-type]
        readonly=payload["readonly"],  # type: ignore[arg-type]
    )
    reason_codes = _payload_reason_codes(payload["reason_codes"])
    expected_reason_codes = _reason_codes_for_input(source)
    if reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match ambiguity inputs")
    ambiguity_status = _require_member(
        "ambiguity_status",
        payload["ambiguity_status"],
        AMBIGUITY_STATUSES,
    )
    expected_status = _status_for_reason_codes(reason_codes)
    if ambiguity_status != expected_status:
        raise ValueError("ambiguity_status must match reason_codes")
    manual_next_step = _require_member(
        "manual_next_step",
        payload["manual_next_step"],
        MANUAL_NEXT_STEPS,
    )
    if manual_next_step != _manual_next_step_for_status(ambiguity_status):
        raise ValueError("manual_next_step must match ambiguity_status")
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    _require_sha256("payload_digest", payload["payload_digest"])
    payload_without_digest = dict(payload)
    payload_without_digest.pop("payload_digest")
    if payload["payload_digest"] != _digest_from_payload(payload_without_digest):
        raise ValueError("payload_digest does not match public payload")
    return payload


def _reason_codes_for_input(
    ambiguity_input: MarketResolutionAmbiguityEscalationInput,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if ambiguity_input.resolution_rule_clarity < _LOW_CLARITY:
        reason_codes.append("resolution_rule_clarity_low")
    elif ambiguity_input.resolution_rule_clarity < _PARTIAL_CLARITY:
        reason_codes.append("resolution_rule_clarity_partial")
    if ambiguity_input.oracle_dependency_count > _ZERO:
        reason_codes.append("oracle_dependency_present")
    if ambiguity_input.ambiguous_terms_count > _ZERO:
        reason_codes.append("ambiguous_resolution_terms_present")
    if ambiguity_input.source_conflict_count > _ZERO:
        reason_codes.append("conflicting_resolution_sources_present")
    if ambiguity_input.time_to_resolution_hours <= _IMMINENT_RESOLUTION_HOURS:
        reason_codes.append("resolution_window_imminent")
    if not reason_codes:
        reason_codes.append(READY_REASON_CODE)
    return _normalize_reason_codes(tuple(reason_codes))


def _status_for_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if READY_REASON_CODE in reason_codes:
        return "clear"
    escalation_reasons = {
        "resolution_rule_clarity_low",
        "conflicting_resolution_sources_present",
        "resolution_window_imminent",
    }
    if "resolution_window_imminent" in reason_codes and any(
        reason in reason_codes
        for reason in (
            "resolution_rule_clarity_low",
            "conflicting_resolution_sources_present",
            "ambiguous_resolution_terms_present",
        )
    ):
        return "escalate"
    if len(escalation_reasons.intersection(reason_codes)) >= 2:
        return "escalate"
    return "manual_review"


def _manual_next_step_for_status(ambiguity_status: str) -> str:
    if ambiguity_status == "clear":
        return "continue_readonly_monitoring"
    if ambiguity_status == "manual_review":
        return "queue_manual_resolution_review"
    if ambiguity_status == "escalate":
        return "escalate_to_manual_resolution_review"
    raise ValueError("ambiguity_status must be supported")


def _payload_without_digest(
    report: MarketResolutionAmbiguityEscalationReport,
) -> dict[str, object]:
    payload = _json_payload(
        {
            "config_version": report.config_version,
            "resolution_rule_clarity": report.resolution_rule_clarity,
            "oracle_dependency_count": report.oracle_dependency_count,
            "ambiguous_terms_count": report.ambiguous_terms_count,
            "source_conflict_count": report.source_conflict_count,
            "time_to_resolution_hours": report.time_to_resolution_hours,
            "ambiguity_status": report.ambiguity_status,
            "reason_codes": report.reason_codes,
            "manual_next_step": report.manual_next_step,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )
    return payload


def _json_payload(values: dict[str, object]) -> dict[str, object]:
    payload = json_ready_no_floats(values)
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    _reject_unsafe_public_values(payload)
    return payload


def _validate_report(report: MarketResolutionAmbiguityEscalationReport) -> None:
    source = MarketResolutionAmbiguityEscalationInput(
        resolution_rule_clarity=report.resolution_rule_clarity,
        oracle_dependency_count=report.oracle_dependency_count,
        ambiguous_terms_count=report.ambiguous_terms_count,
        source_conflict_count=report.source_conflict_count,
        time_to_resolution_hours=report.time_to_resolution_hours,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    expected_reason_codes = _reason_codes_for_input(source)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match ambiguity inputs")
    expected_status = _status_for_reason_codes(report.reason_codes)
    if report.ambiguity_status != expected_status:
        raise ValueError("ambiguity_status must match reason_codes")
    if report.manual_next_step != _manual_next_step_for_status(report.ambiguity_status):
        raise ValueError("manual_next_step must match ambiguity_status")


def _payload_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is list:
        return _normalize_reason_codes(tuple(value))
    if type(value) is tuple:
        return _normalize_reason_codes(value)
    raise ValueError("reason_codes must be a list")


def _normalize_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    seen: set[str] = set()
    for reason_code in value:
        if type(reason_code) is not str or reason_code not in REASON_CODE_SEQUENCE:
            raise ValueError("reason_codes contains unsupported reason code")
        if reason_code in seen:
            raise ValueError("reason_codes must not contain duplicates")
        _require_public_string("reason_codes", reason_code)
        seen.add(reason_code)
    ordered = tuple(reason for reason in REASON_CODE_SEQUENCE if reason in seen)
    if value != ordered:
        raise ValueError("reason_codes must use canonical order")
    if READY_REASON_CODE in ordered and ordered != (READY_REASON_CODE,):
        raise ValueError("ready reason code must stand alone")
    return ordered


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_member(
    field_name: str,
    value: object,
    supported_values: tuple[str, ...],
) -> str:
    if type(value) is not str or value not in supported_values:
        raise ValueError(f"{field_name} must be supported")
    _require_public_string(field_name, value)
    return value


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} must not contain unsafe public text")


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > _ONE:
        raise ValueError(f"{field_name} must be less than or equal to 1")
    return normalized


def _payload_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be serialized as a string")
    return _require_nonnegative_decimal(field_name, Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANT)


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _digest_from_payload(payload: dict[str, object]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def _reject_unsafe_public_values(value: object) -> None:
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_unsafe_public_values(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_values(item)
        return
    if type(value) is str:
        normalized = value.lower()
        if any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError("public payload contains unsafe public value")


__all__ = (
    "DEFAULT_MARKET_RESOLUTION_AMBIGUITY_ESCALATION_VERSION",
    "MarketResolutionAmbiguityEscalationInput",
    "MarketResolutionAmbiguityEscalationReport",
    "build_market_resolution_ambiguity_escalation_report",
    "market_resolution_ambiguity_escalation_payload",
    "market_resolution_ambiguity_escalation_payload_digest",
    "validate_market_resolution_ambiguity_escalation_payload",
)
