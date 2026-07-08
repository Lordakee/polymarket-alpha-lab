"""Public-safe false-positive audit for event trigger quality."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal, ROUND_HALF_EVEN
import hashlib
import json
from typing import Any


STATUSES = ("pass", "watch", "block")

PASS_REASON = "event_trigger_false_positive_audit_pass"
WATCH_REASON = "false_positive_risk_watch"
BLOCK_REASON = "false_positive_risk_block"

REASON_CODES = (
    PASS_REASON,
    WATCH_REASON,
    BLOCK_REASON,
    "aggregate_catalyst_quality_weak",
    "aggregate_catalyst_quality_low",
    "source_reliability_weak",
    "source_reliability_low",
    "contradiction_count_elevated",
    "contradiction_count_high",
    "historical_trigger_precision_weak",
    "historical_trigger_precision_low",
    "rule_clarity_weak",
    "rule_clarity_low",
)

SCORE_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

WATCH_SCORE = Decimal("0.250000")
BLOCK_SCORE = Decimal("0.600000")
WEAK_SCORE = Decimal("0.700000")
LOW_SCORE = Decimal("0.500000")
ELEVATED_CONTRADICTIONS = Decimal("2.000000")
HIGH_CONTRADICTIONS = Decimal("4.000000")

UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "eventid",
        "eventslug",
        "marketid",
        "marketslug",
        "conditionid",
        "clobtoken",
        "sourceid",
        "sourceurl",
        "title",
        "url",
        "slug",
    ),
)

__all__ = (
    "STATUSES",
    "ResearchEventTriggerFalsePositiveAuditInput",
    "ResearchEventTriggerFalsePositiveAuditReport",
    "build_research_event_trigger_false_positive_audit_report",
    "research_event_trigger_false_positive_audit_report_payload",
    "validate_research_event_trigger_false_positive_audit_public_payload",
)


@dataclass(frozen=True)
class ResearchEventTriggerFalsePositiveAuditInput:
    aggregate_catalyst_quality_score: Decimal
    source_reliability_score: Decimal
    contradiction_count: Decimal
    historical_trigger_precision: Decimal
    rule_clarity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "aggregate_catalyst_quality_score",
            "source_reliability_score",
            "historical_trigger_precision",
            "rule_clarity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "contradiction_count",
            _require_count("contradiction_count", self.contradiction_count),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchEventTriggerFalsePositiveAuditReport:
    aggregate_catalyst_quality_score: Decimal
    source_reliability_score: Decimal
    contradiction_count: Decimal
    historical_trigger_precision: Decimal
    rule_clarity_score: Decimal
    false_positive_risk_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "aggregate_catalyst_quality_score",
            "source_reliability_score",
            "historical_trigger_precision",
            "rule_clarity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "contradiction_count",
            _require_count("contradiction_count", self.contradiction_count),
        )
        object.__setattr__(
            self,
            "false_positive_risk_score",
            _require_ratio(
                "false_positive_risk_score",
                self.false_positive_risk_score,
            ),
        )
        _require_status(self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("report", self)
        _validate_report(self)
        expected_digest = _digest_payload(_payload_without_digest(self))
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _reject_unsafe_public_surface("report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_event_trigger_false_positive_audit_report_payload(self)


def build_research_event_trigger_false_positive_audit_report(
    audit_input: ResearchEventTriggerFalsePositiveAuditInput,
) -> ResearchEventTriggerFalsePositiveAuditReport:
    if type(audit_input) is not ResearchEventTriggerFalsePositiveAuditInput:
        raise ValueError(
            "audit_input must be a ResearchEventTriggerFalsePositiveAuditInput",
        )
    _require_hard_flags("input", audit_input)
    risk_score = _false_positive_risk_score(audit_input)
    return ResearchEventTriggerFalsePositiveAuditReport(
        aggregate_catalyst_quality_score=audit_input.aggregate_catalyst_quality_score,
        source_reliability_score=audit_input.source_reliability_score,
        contradiction_count=audit_input.contradiction_count,
        historical_trigger_precision=audit_input.historical_trigger_precision,
        rule_clarity_score=audit_input.rule_clarity_score,
        false_positive_risk_score=risk_score,
        status=_status_for_inputs(audit_input, risk_score),
        reason_codes=_reason_codes_for_inputs(audit_input, risk_score),
    )


def research_event_trigger_false_positive_audit_report_payload(
    report: ResearchEventTriggerFalsePositiveAuditReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventTriggerFalsePositiveAuditReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_surface("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchEventTriggerFalsePositiveAuditReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_event_trigger_false_positive_audit_public_payload(payload)
    return payload


def validate_research_event_trigger_false_positive_audit_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_surface("payload", payload)
    _reject_public_numerics(payload)
    _require_hard_flags("payload", _PayloadFlags(payload))
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    payload_without_digest = dict(payload)
    payload_without_digest.pop("derived_validation_digest", None)
    expected_digest = _digest_payload(payload_without_digest)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest does not match public payload")


def _false_positive_risk_score(
    audit_input: ResearchEventTriggerFalsePositiveAuditInput,
) -> Decimal:
    score = (
        (ONE - audit_input.aggregate_catalyst_quality_score) * Decimal("0.218000")
        + (ONE - audit_input.source_reliability_score) * Decimal("0.210000")
        + (ONE - audit_input.historical_trigger_precision) * Decimal("0.250000")
        + (ONE - audit_input.rule_clarity_score) * Decimal("0.150000")
        + audit_input.contradiction_count * Decimal("0.033900")
        - audit_input.contradiction_count
        * audit_input.contradiction_count
        * Decimal("0.000120")
    )
    if score < ZERO:
        return ZERO
    if score > ONE:
        return ONE
    return score.quantize(SCORE_QUANTUM, rounding=ROUND_HALF_EVEN)


def _status_for_inputs(
    audit_input: ResearchEventTriggerFalsePositiveAuditInput,
    risk_score: Decimal,
) -> str:
    if (
        risk_score >= BLOCK_SCORE
        or audit_input.aggregate_catalyst_quality_score < LOW_SCORE
        or audit_input.source_reliability_score < LOW_SCORE
        or audit_input.historical_trigger_precision < LOW_SCORE
        or audit_input.rule_clarity_score < LOW_SCORE
        or audit_input.contradiction_count >= HIGH_CONTRADICTIONS
    ):
        return "block"
    if (
        risk_score >= WATCH_SCORE
        or audit_input.aggregate_catalyst_quality_score < WEAK_SCORE
        or audit_input.source_reliability_score < WEAK_SCORE
        or audit_input.historical_trigger_precision < WEAK_SCORE
        or audit_input.rule_clarity_score < WEAK_SCORE
        or audit_input.contradiction_count >= ELEVATED_CONTRADICTIONS
    ):
        return "watch"
    return "pass"


def _reason_codes_for_inputs(
    audit_input: ResearchEventTriggerFalsePositiveAuditInput,
    risk_score: Decimal,
) -> tuple[str, ...]:
    status = _status_for_inputs(audit_input, risk_score)
    if status == "pass":
        return (PASS_REASON,)

    reasons = [BLOCK_REASON if status == "block" else WATCH_REASON]
    _append_quality_reason(
        reasons,
        "aggregate_catalyst_quality",
        audit_input.aggregate_catalyst_quality_score,
    )
    _append_quality_reason(
        reasons,
        "source_reliability",
        audit_input.source_reliability_score,
    )
    if audit_input.contradiction_count >= HIGH_CONTRADICTIONS:
        reasons.append("contradiction_count_high")
    elif audit_input.contradiction_count >= ELEVATED_CONTRADICTIONS:
        reasons.append("contradiction_count_elevated")
    _append_quality_reason(
        reasons,
        "historical_trigger_precision",
        audit_input.historical_trigger_precision,
    )
    _append_quality_reason(reasons, "rule_clarity", audit_input.rule_clarity_score)
    return _normalize_reason_codes(tuple(reasons))


def _append_quality_reason(reasons: list[str], prefix: str, value: Decimal) -> None:
    if value < LOW_SCORE:
        reasons.append(f"{prefix}_low")
    elif value < WEAK_SCORE:
        reasons.append(f"{prefix}_weak")


def _validate_report(report: ResearchEventTriggerFalsePositiveAuditReport) -> None:
    audit_input = ResearchEventTriggerFalsePositiveAuditInput(
        aggregate_catalyst_quality_score=report.aggregate_catalyst_quality_score,
        source_reliability_score=report.source_reliability_score,
        contradiction_count=report.contradiction_count,
        historical_trigger_precision=report.historical_trigger_precision,
        rule_clarity_score=report.rule_clarity_score,
    )
    expected_score = _false_positive_risk_score(audit_input)
    if report.false_positive_risk_score != expected_score:
        raise ValueError("false_positive_risk_score must match inputs")
    if report.status != _status_for_inputs(audit_input, expected_score):
        raise ValueError("status must match false-positive risk inputs")
    if report.reason_codes != _reason_codes_for_inputs(audit_input, expected_score):
        raise ValueError("reason_codes must match false-positive risk inputs")


def _payload_without_digest(
    report: ResearchEventTriggerFalsePositiveAuditReport,
) -> dict[str, Any]:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _digest_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class _PayloadFlags:
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


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        normalized = value.quantize(SCORE_QUANTUM, rounding=ROUND_HALF_EVEN)
    except Decimal.InvalidOperation as exc:
        raise ValueError(f"{field_name} precision is too granular") from exc
    if normalized != value:
        raise ValueError(f"{field_name} precision is too granular")
    return normalized


def _require_ratio(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_count(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value(rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized.quantize(COUNT_QUANTUM, rounding=ROUND_HALF_EVEN)


def _require_status(value: object) -> None:
    if value not in STATUSES:
        raise ValueError("status must be pass, watch, or block")


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for reason_code in reason_codes:
        if type(reason_code) is not str:
            raise ValueError("reason_codes entries must be strings")
        if reason_code not in REASON_CODES:
            raise ValueError("reason_codes entries must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in normalized)


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, float) or type(value) is int:
        raise ValueError("JSON value must use Decimal-derived strings")
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_surface(label, asdict(value))
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_public_surface(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_surface(label, item)


def _reject_public_numerics(value: object) -> None:
    if isinstance(value, float) or type(value) is int:
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = "".join(character for character in value.lower() if character.isalnum())
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)
