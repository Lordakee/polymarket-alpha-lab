"""Read-only settlement delay and capital lockup risk report."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re


__all__ = (
    "PROBABILITY_EVENT_SETTLEMENT_DELAY_RISK_REPORT_VERSION",
    "ProbabilityEventSettlementDelayRiskInput",
    "ProbabilityEventSettlementDelayRiskPublicPayload",
    "ProbabilityEventSettlementDelayRiskReport",
    "build_probability_event_settlement_delay_risk_report",
    "probability_event_settlement_delay_risk_report_digest",
    "probability_event_settlement_delay_risk_report_payload",
    "validate_probability_event_settlement_delay_risk_public_payload",
)


PROBABILITY_EVENT_SETTLEMENT_DELAY_RISK_REPORT_VERSION = (
    "probability-event-settlement-delay-risk-report-v0"
)

Q = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
EXPECTED_WINDOW_WATCH_HOURS = Decimal("48.000000")
EXPECTED_WINDOW_BLOCK_HOURS = Decimal("72.000000")
HISTORICAL_DELAY_WATCH_HOURS = Decimal("12.000000")
HISTORICAL_DELAY_BLOCK_HOURS = Decimal("24.000000")
ORACLE_DEPENDENCY_WATCH_COUNT = Decimal("1.000000")
ORACLE_DEPENDENCY_BLOCK_COUNT = Decimal("3.000000")
AMBIGUOUS_RULE_WATCH_COUNT = Decimal("1.000000")
AMBIGUOUS_RULE_BLOCK_COUNT = Decimal("2.000000")
CAPITAL_LOCKUP_WATCH_PROBABILITY = Decimal("0.250000")
CAPITAL_LOCKUP_BLOCK_PROBABILITY = Decimal("0.500000")
EXPECTED_DELAY_BLOCK_HOURS = Decimal("168.000000")
ORACLE_DEPENDENCY_DELAY_HOURS = Decimal("12.000000")
AMBIGUOUS_RULE_DELAY_HOURS = Decimal("62.000000") / Decimal("3.000000")
CAPITAL_LOCKUP_DELAY_HOURS = Decimal("48.000000")

PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")

STATUSES = ("pass", "watch", "block")
REASON_CODES = (
    "settlement_delay_risk_pass",
    "expected_resolution_window_extended",
    "historical_settlement_delay_observed",
    "oracle_dependency_delay_risk",
    "ambiguous_resolution_rule_delay_risk",
    "capital_lockup_probability_high",
)
MANUAL_NEXT_STEPS = (
    "monitor_public_resolution_timeline",
    "prepare_manual_settlement_delay_review",
    "pause_new_capital_until_resolution_risk_review",
)
PAYLOAD_FIELDS = (
    "config_version",
    "delay_risk_status",
    "expected_resolution_hours",
    "historical_delay_hours",
    "oracle_dependency_count",
    "ambiguous_rule_count",
    "capital_lockup_probability",
    "expected_settlement_delay_hours",
    "reason_codes",
    "manual_next_step",
    "paper_only",
    "report_only",
    "readonly",
    "payload_digest",
)


class ProbabilityEventSettlementDelayRiskPublicPayload(dict[str, object]):
    """Immutable public payload for the settlement delay risk report."""

    def _no_change(self, *args: object, **kwargs: object) -> None:
        raise TypeError("public_payload is immutable")

    __setitem__ = _no_change
    __delitem__ = _no_change
    clear = _no_change
    pop = _no_change
    popitem = _no_change
    setdefault = _no_change
    update = _no_change


@dataclass(frozen=True)
class ProbabilityEventSettlementDelayRiskInput:
    expected_resolution_hours: Decimal
    historical_delay_hours: Decimal
    oracle_dependency_count: Decimal
    ambiguous_rule_count: Decimal
    capital_lockup_probability: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventSettlementDelayRiskInput:
            raise TypeError(
                "ProbabilityEventSettlementDelayRiskInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventSettlementDelayRiskInput:
            raise ValueError(
                "input must be exactly ProbabilityEventSettlementDelayRiskInput",
            )
        object.__setattr__(
            self,
            "expected_resolution_hours",
            _require_nonnegative_decimal(
                "expected_resolution_hours",
                self.expected_resolution_hours,
            ),
        )
        object.__setattr__(
            self,
            "historical_delay_hours",
            _require_nonnegative_decimal(
                "historical_delay_hours",
                self.historical_delay_hours,
            ),
        )
        object.__setattr__(
            self,
            "oracle_dependency_count",
            _require_count_decimal(
                "oracle_dependency_count",
                self.oracle_dependency_count,
            ),
        )
        object.__setattr__(
            self,
            "ambiguous_rule_count",
            _require_count_decimal(
                "ambiguous_rule_count",
                self.ambiguous_rule_count,
            ),
        )
        object.__setattr__(
            self,
            "capital_lockup_probability",
            _require_ratio_decimal(
                "capital_lockup_probability",
                self.capital_lockup_probability,
            ),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ProbabilityEventSettlementDelayRiskReport:
    config_version: str
    delay_risk_status: str
    expected_resolution_hours: Decimal
    historical_delay_hours: Decimal
    oracle_dependency_count: Decimal
    ambiguous_rule_count: Decimal
    capital_lockup_probability: Decimal
    expected_settlement_delay_hours: Decimal
    reason_codes: tuple[str, ...]
    manual_next_step: str
    public_payload: ProbabilityEventSettlementDelayRiskPublicPayload
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventSettlementDelayRiskReport:
            raise TypeError(
                "ProbabilityEventSettlementDelayRiskReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventSettlementDelayRiskReport:
            raise ValueError(
                "report must be exactly ProbabilityEventSettlementDelayRiskReport",
            )
        _require_public_label("config_version", self.config_version)
        if self.config_version != PROBABILITY_EVENT_SETTLEMENT_DELAY_RISK_REPORT_VERSION:
            raise ValueError("config_version must be the report version")
        _require_status(self.delay_risk_status)
        object.__setattr__(
            self,
            "expected_resolution_hours",
            _require_nonnegative_decimal(
                "expected_resolution_hours",
                self.expected_resolution_hours,
            ),
        )
        object.__setattr__(
            self,
            "historical_delay_hours",
            _require_nonnegative_decimal(
                "historical_delay_hours",
                self.historical_delay_hours,
            ),
        )
        object.__setattr__(
            self,
            "oracle_dependency_count",
            _require_count_decimal(
                "oracle_dependency_count",
                self.oracle_dependency_count,
            ),
        )
        object.__setattr__(
            self,
            "ambiguous_rule_count",
            _require_count_decimal(
                "ambiguous_rule_count",
                self.ambiguous_rule_count,
            ),
        )
        object.__setattr__(
            self,
            "capital_lockup_probability",
            _require_ratio_decimal(
                "capital_lockup_probability",
                self.capital_lockup_probability,
            ),
        )
        object.__setattr__(
            self,
            "expected_settlement_delay_hours",
            _require_nonnegative_decimal(
                "expected_settlement_delay_hours",
                self.expected_settlement_delay_hours,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_manual_next_step(self.manual_next_step)
        _require_digest("payload_digest", self.payload_digest)
        _require_hard_flags(self)
        _validate_report(self)
        expected_digest = _payload_digest(
            _payload_values(_report_values_without_payload(self), ""),
        )
        if self.payload_digest != expected_digest:
            raise ValueError("payload_digest must match public payload")
        expected_payload = ProbabilityEventSettlementDelayRiskPublicPayload(
            _payload_values(_report_values_without_payload(self), self.payload_digest),
        )
        validate_probability_event_settlement_delay_risk_public_payload(
            self.public_payload,
        )
        if dict(self.public_payload) != dict(expected_payload):
            raise ValueError("public_payload must match report fields")


def build_probability_event_settlement_delay_risk_report(
    inputs: ProbabilityEventSettlementDelayRiskInput,
) -> ProbabilityEventSettlementDelayRiskReport:
    """Build a deterministic read-only settlement delay risk report."""

    if type(inputs) is not ProbabilityEventSettlementDelayRiskInput:
        raise ValueError(
            "inputs must be a ProbabilityEventSettlementDelayRiskInput",
        )
    _require_hard_flags(inputs)
    values: dict[str, object] = {
        "config_version": PROBABILITY_EVENT_SETTLEMENT_DELAY_RISK_REPORT_VERSION,
        "expected_resolution_hours": inputs.expected_resolution_hours,
        "historical_delay_hours": inputs.historical_delay_hours,
        "oracle_dependency_count": inputs.oracle_dependency_count,
        "ambiguous_rule_count": inputs.ambiguous_rule_count,
        "capital_lockup_probability": inputs.capital_lockup_probability,
    }
    expected_delay = _expected_settlement_delay_hours(inputs)
    reason_codes = _reason_codes(inputs)
    status = _delay_risk_status(inputs, expected_delay, reason_codes)
    values.update(
        {
            "delay_risk_status": status,
            "expected_settlement_delay_hours": expected_delay,
            "reason_codes": reason_codes,
            "manual_next_step": _manual_next_step(status),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )
    payload_digest = _payload_digest(_payload_values(values, ""))
    public_payload = ProbabilityEventSettlementDelayRiskPublicPayload(
        _payload_values(values, payload_digest),
    )
    return ProbabilityEventSettlementDelayRiskReport(
        public_payload=public_payload,
        payload_digest=payload_digest,
        **values,
    )


def probability_event_settlement_delay_risk_report_payload(
    report: ProbabilityEventSettlementDelayRiskReport,
) -> ProbabilityEventSettlementDelayRiskPublicPayload:
    if type(report) is not ProbabilityEventSettlementDelayRiskReport:
        raise ValueError(
            "report must be a ProbabilityEventSettlementDelayRiskReport",
        )
    _require_hard_flags(report)
    _validate_report(report)
    expected_digest = probability_event_settlement_delay_risk_report_digest(report)
    if report.payload_digest != expected_digest:
        raise ValueError("payload_digest must match report payload")
    validate_probability_event_settlement_delay_risk_public_payload(
        report.public_payload,
    )
    return report.public_payload


def probability_event_settlement_delay_risk_report_digest(
    report: ProbabilityEventSettlementDelayRiskReport,
) -> str:
    if type(report) is not ProbabilityEventSettlementDelayRiskReport:
        raise ValueError(
            "report must be a ProbabilityEventSettlementDelayRiskReport",
        )
    _require_hard_flags(report)
    _validate_report(report)
    return _payload_digest(_payload_values(_report_values_without_payload(report), ""))


def validate_probability_event_settlement_delay_risk_public_payload(
    payload: Mapping[str, object],
) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    if tuple(payload) != PAYLOAD_FIELDS:
        raise ValueError("payload must match the settlement delay risk schema")
    _require_public_label("config_version", payload["config_version"])
    if payload["config_version"] != PROBABILITY_EVENT_SETTLEMENT_DELAY_RISK_REPORT_VERSION:
        raise ValueError("config_version must be the report version")
    _require_status(payload["delay_risk_status"])
    _require_payload_decimal_text(
        "expected_resolution_hours",
        payload["expected_resolution_hours"],
        _require_nonnegative_decimal,
    )
    _require_payload_decimal_text(
        "historical_delay_hours",
        payload["historical_delay_hours"],
        _require_nonnegative_decimal,
    )
    _require_payload_decimal_text(
        "oracle_dependency_count",
        payload["oracle_dependency_count"],
        _require_count_decimal,
    )
    _require_payload_decimal_text(
        "ambiguous_rule_count",
        payload["ambiguous_rule_count"],
        _require_count_decimal,
    )
    _require_payload_decimal_text(
        "capital_lockup_probability",
        payload["capital_lockup_probability"],
        _require_ratio_decimal,
    )
    _require_payload_decimal_text(
        "expected_settlement_delay_hours",
        payload["expected_settlement_delay_hours"],
        _require_nonnegative_decimal,
    )
    _normalize_reason_codes(payload["reason_codes"])
    _require_manual_next_step(payload["manual_next_step"])
    for flag_name in ("paper_only", "report_only", "readonly"):
        _require_bool(flag_name, payload[flag_name])
        if payload[flag_name] is not True:
            raise ValueError(f"{flag_name} must be True")
    digest = payload["payload_digest"]
    _require_digest("payload_digest", digest)
    payload_without_digest = dict(payload)
    payload_without_digest["payload_digest"] = ""
    if digest != _payload_digest(payload_without_digest):
        raise ValueError("payload_digest must match public payload")
    return payload


def _validate_report(report: ProbabilityEventSettlementDelayRiskReport) -> None:
    inputs = ProbabilityEventSettlementDelayRiskInput(
        expected_resolution_hours=report.expected_resolution_hours,
        historical_delay_hours=report.historical_delay_hours,
        oracle_dependency_count=report.oracle_dependency_count,
        ambiguous_rule_count=report.ambiguous_rule_count,
        capital_lockup_probability=report.capital_lockup_probability,
    )
    expected_delay = _expected_settlement_delay_hours(inputs)
    reason_codes = _reason_codes(inputs)
    status = _delay_risk_status(inputs, expected_delay, reason_codes)
    if report.expected_settlement_delay_hours != expected_delay:
        raise ValueError("expected_settlement_delay_hours must match inputs")
    if report.reason_codes != reason_codes:
        raise ValueError("reason_codes must match inputs")
    if report.delay_risk_status != status:
        raise ValueError("delay_risk_status must match inputs")
    if report.manual_next_step != _manual_next_step(status):
        raise ValueError("manual_next_step must match delay_risk_status")


def _expected_settlement_delay_hours(
    inputs: ProbabilityEventSettlementDelayRiskInput,
) -> Decimal:
    return _q(
        inputs.expected_resolution_hours
        + inputs.historical_delay_hours
        + (inputs.oracle_dependency_count * ORACLE_DEPENDENCY_DELAY_HOURS)
        + (inputs.ambiguous_rule_count * AMBIGUOUS_RULE_DELAY_HOURS)
        + (inputs.capital_lockup_probability * CAPITAL_LOCKUP_DELAY_HOURS),
    )


def _reason_codes(
    inputs: ProbabilityEventSettlementDelayRiskInput,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if inputs.expected_resolution_hours >= EXPECTED_WINDOW_BLOCK_HOURS:
        reasons.append("expected_resolution_window_extended")
    elif inputs.expected_resolution_hours >= EXPECTED_WINDOW_WATCH_HOURS:
        reasons.append("expected_resolution_window_extended")
    if inputs.historical_delay_hours >= HISTORICAL_DELAY_BLOCK_HOURS:
        reasons.append("historical_settlement_delay_observed")
    elif inputs.historical_delay_hours >= HISTORICAL_DELAY_WATCH_HOURS:
        reasons.append("historical_settlement_delay_observed")
    if inputs.oracle_dependency_count >= ORACLE_DEPENDENCY_WATCH_COUNT:
        reasons.append("oracle_dependency_delay_risk")
    if inputs.ambiguous_rule_count >= AMBIGUOUS_RULE_WATCH_COUNT:
        reasons.append("ambiguous_resolution_rule_delay_risk")
    if inputs.capital_lockup_probability >= CAPITAL_LOCKUP_WATCH_PROBABILITY:
        reasons.append("capital_lockup_probability_high")
    if not reasons:
        return ("settlement_delay_risk_pass",)
    return tuple(reasons)


def _delay_risk_status(
    inputs: ProbabilityEventSettlementDelayRiskInput,
    expected_delay: Decimal,
    reason_codes: tuple[str, ...],
) -> str:
    if reason_codes == ("settlement_delay_risk_pass",):
        return "pass"
    if (
        expected_delay >= EXPECTED_DELAY_BLOCK_HOURS
        or inputs.expected_resolution_hours >= EXPECTED_WINDOW_BLOCK_HOURS
        or inputs.historical_delay_hours >= HISTORICAL_DELAY_BLOCK_HOURS
        or inputs.oracle_dependency_count >= ORACLE_DEPENDENCY_BLOCK_COUNT
        or inputs.ambiguous_rule_count >= AMBIGUOUS_RULE_BLOCK_COUNT
        or inputs.capital_lockup_probability >= CAPITAL_LOCKUP_BLOCK_PROBABILITY
    ):
        return "block"
    return "watch"


def _manual_next_step(status: str) -> str:
    if status == "pass":
        return "monitor_public_resolution_timeline"
    if status == "watch":
        return "prepare_manual_settlement_delay_review"
    if status == "block":
        return "pause_new_capital_until_resolution_risk_review"
    raise ValueError("delay_risk_status must be pass, watch, or block")


def _report_values_without_payload(
    report: ProbabilityEventSettlementDelayRiskReport,
) -> dict[str, object]:
    return {
        "config_version": report.config_version,
        "delay_risk_status": report.delay_risk_status,
        "expected_resolution_hours": report.expected_resolution_hours,
        "historical_delay_hours": report.historical_delay_hours,
        "oracle_dependency_count": report.oracle_dependency_count,
        "ambiguous_rule_count": report.ambiguous_rule_count,
        "capital_lockup_probability": report.capital_lockup_probability,
        "expected_settlement_delay_hours": report.expected_settlement_delay_hours,
        "reason_codes": report.reason_codes,
        "manual_next_step": report.manual_next_step,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _payload_values(values: Mapping[str, object], payload_digest: str) -> dict[str, object]:
    return {
        "config_version": values["config_version"],
        "delay_risk_status": values["delay_risk_status"],
        "expected_resolution_hours": _decimal_text(values["expected_resolution_hours"]),
        "historical_delay_hours": _decimal_text(values["historical_delay_hours"]),
        "oracle_dependency_count": _decimal_text(values["oracle_dependency_count"]),
        "ambiguous_rule_count": _decimal_text(values["ambiguous_rule_count"]),
        "capital_lockup_probability": _decimal_text(
            values["capital_lockup_probability"],
        ),
        "expected_settlement_delay_hours": _decimal_text(
            values["expected_settlement_delay_hours"],
        ),
        "reason_codes": values["reason_codes"],
        "manual_next_step": values["manual_next_step"],
        "paper_only": values["paper_only"],
        "report_only": values["report_only"],
        "readonly": values["readonly"],
        "payload_digest": payload_digest,
    }


def _payload_digest(payload: Mapping[str, object]) -> str:
    canonical = json.dumps(
        payload,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _require_payload_decimal_text(
    field_name: str,
    value: object,
    checker: object,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be serialized as a string")
    return checker(field_name, Decimal(value))  # type: ignore[operator]


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-number Decimal")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _q(value)


def _decimal_text(value: object) -> str:
    if type(value) is not Decimal:
        raise ValueError("public numeric values must be Decimal before serialization")
    return f"{_q(value):.6f}"


def _q(value: Decimal) -> Decimal:
    return value.quantize(Q, rounding=ROUND_HALF_UP)


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not value:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in value:
        if type(reason_code) is not str:
            raise ValueError("reason_codes must contain strings")
        if reason_code not in REASON_CODES:
            raise ValueError("reason_codes contains an unsupported value")
        if reason_code in seen:
            raise ValueError("reason_codes must not contain duplicates")
        seen.add(reason_code)
        normalized.append(reason_code)
    return tuple(normalized)


def _require_status(value: object) -> str:
    if type(value) is not str:
        raise ValueError("delay_risk_status must be a string")
    if value not in STATUSES:
        raise ValueError("delay_risk_status must be pass, watch, or block")
    return value


def _require_manual_next_step(value: object) -> str:
    if type(value) is not str:
        raise ValueError("manual_next_step must be a string")
    if value not in MANUAL_NEXT_STEPS:
        raise ValueError("manual_next_step must be a supported value")
    return value


def _require_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_hard_flags(value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        flag_value = getattr(value, flag_name)
        _require_bool(flag_name, flag_value)
        if flag_value is not True:
            raise ValueError(f"{flag_name} must be True")


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public label")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value
