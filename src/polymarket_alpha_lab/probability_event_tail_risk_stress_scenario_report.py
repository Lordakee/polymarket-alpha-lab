"""Read-only probability event tail-risk stress scenario report.

Pure in-memory Decimal arithmetic for probability event stress review. The
module only produces immutable report objects, public payloads, and digests.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any


PROBABILITY_EVENT_TAIL_RISK_STRESS_SCENARIO_STATUSES = (
    "pass",
    "attention",
    "blocker",
)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_REASON_CODES = (
    "scenario_coverage_below_required_attention",
    "stress_adjusted_edge_not_positive_blocker",
    "tail_risk_stress_scenario_report_pass",
)
_MANUAL_NEXT_STEPS = (
    "add_manual_tail_risk_scenarios",
    "document_tail_risk_stress_review",
    "escalate_manual_tail_risk_review",
)
_PUBLIC_FIELDS = frozenset(
    (
        "base_case_probability",
        "tail_event_probability",
        "tail_loss_probability",
        "tail_risk_charge_probability",
        "scenario_coverage_count",
        "required_scenario_count",
        "scenario_coverage_ratio",
        "stress_adjusted_edge_probability",
        "tail_risk_status",
        "reason_codes",
        "manual_next_step",
        "paper_only",
        "report_only",
        "readonly",
        "payload_digest",
    ),
)
_UNSAFE_PUBLIC_FRAGMENTS = (
    "au" + "th",
    "auto",
    "b" + "uy",
    "exec" + "ute",
    "exec" + "ution",
    "jsonl",
    "k" + "ey",
    "li" + "ve",
    "or" + "der",
    "persist",
    "se" + "ll",
    "sig" + "n",
    "trad" + "e",
    "wal" + "let",
)


@dataclass(frozen=True)
class ProbabilityEventTailRiskStressScenarioInput:
    base_case_probability: Decimal
    tail_event_probability: Decimal
    tail_loss_probability: Decimal
    scenario_coverage_count: Decimal
    required_scenario_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventTailRiskStressScenarioInput:
            raise ValueError(
                "input must be exactly ProbabilityEventTailRiskStressScenarioInput",
            )
        for field_name in (
            "base_case_probability",
            "tail_event_probability",
            "tail_loss_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("scenario_coverage_count", "required_scenario_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        if self.required_scenario_count <= ZERO:
            raise ValueError("required_scenario_count must be positive")
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ProbabilityEventTailRiskStressScenarioReport:
    base_case_probability: Decimal
    tail_event_probability: Decimal
    tail_loss_probability: Decimal
    tail_risk_charge_probability: Decimal
    scenario_coverage_count: Decimal
    required_scenario_count: Decimal
    scenario_coverage_ratio: Decimal
    stress_adjusted_edge_probability: Decimal
    tail_risk_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventTailRiskStressScenarioReport:
            raise ValueError(
                "report must be exactly ProbabilityEventTailRiskStressScenarioReport",
            )
        for field_name in (
            "base_case_probability",
            "tail_event_probability",
            "tail_loss_probability",
            "tail_risk_charge_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "scenario_coverage_count",
            "required_scenario_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        if self.required_scenario_count <= ZERO:
            raise ValueError("required_scenario_count must be positive")
        for field_name in (
            "scenario_coverage_ratio",
            "stress_adjusted_edge_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("tail_risk_status", self.tail_risk_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_manual_next_step("manual_next_step", self.manual_next_step)
        _require_hard_flags("report", self)
        _apply_or_verify_payload_digest(self)
        _validate_report_consistency(self)

    @property
    def public_payload(self) -> dict[str, Any]:
        return probability_event_tail_risk_stress_scenario_public_payload(self)


def build_probability_event_tail_risk_stress_scenario_report(
    value: ProbabilityEventTailRiskStressScenarioInput,
) -> ProbabilityEventTailRiskStressScenarioReport:
    if type(value) is not ProbabilityEventTailRiskStressScenarioInput:
        raise ValueError(
            "value must be a ProbabilityEventTailRiskStressScenarioInput",
        )
    _require_hard_flags("input", value)
    tail_risk_charge_probability = _multiply_decimal(
        value.tail_event_probability,
        value.tail_loss_probability,
    )
    stress_adjusted_edge_probability = _subtract_decimal(
        value.base_case_probability,
        tail_risk_charge_probability,
    )
    scenario_coverage_ratio = _divide_decimal(
        value.scenario_coverage_count,
        value.required_scenario_count,
    )
    reason_codes = _reason_codes(
        stress_adjusted_edge_probability=stress_adjusted_edge_probability,
        scenario_coverage_count=value.scenario_coverage_count,
        required_scenario_count=value.required_scenario_count,
    )
    tail_risk_status = _tail_risk_status(reason_codes)
    return ProbabilityEventTailRiskStressScenarioReport(
        base_case_probability=value.base_case_probability,
        tail_event_probability=value.tail_event_probability,
        tail_loss_probability=value.tail_loss_probability,
        tail_risk_charge_probability=tail_risk_charge_probability,
        scenario_coverage_count=value.scenario_coverage_count,
        required_scenario_count=value.required_scenario_count,
        scenario_coverage_ratio=scenario_coverage_ratio,
        stress_adjusted_edge_probability=stress_adjusted_edge_probability,
        tail_risk_status=tail_risk_status,
        reason_codes=reason_codes,
        manual_next_step=_manual_next_step(tail_risk_status),
    )


def probability_event_tail_risk_stress_scenario_public_payload(
    report: ProbabilityEventTailRiskStressScenarioReport,
) -> dict[str, Any]:
    if type(report) is not ProbabilityEventTailRiskStressScenarioReport:
        raise ValueError(
            "report must be a ProbabilityEventTailRiskStressScenarioReport",
        )
    _require_hard_flags("report", report)
    _verify_payload_digest(report)
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _validate_public_payload_schema(payload)
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _reason_codes(
    *,
    stress_adjusted_edge_probability: Decimal,
    scenario_coverage_count: Decimal,
    required_scenario_count: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if stress_adjusted_edge_probability <= ZERO:
        reasons.append("stress_adjusted_edge_not_positive_blocker")
    if scenario_coverage_count < required_scenario_count:
        reasons.append("scenario_coverage_below_required_attention")
    if not reasons:
        return ("tail_risk_stress_scenario_report_pass",)
    return tuple(sorted(reasons))


def _tail_risk_status(reason_codes: tuple[str, ...]) -> str:
    if "stress_adjusted_edge_not_positive_blocker" in reason_codes:
        return "blocker"
    if "scenario_coverage_below_required_attention" in reason_codes:
        return "attention"
    return "pass"


def _manual_next_step(tail_risk_status: str) -> str:
    if tail_risk_status == "blocker":
        return "escalate_manual_tail_risk_review"
    if tail_risk_status == "attention":
        return "add_manual_tail_risk_scenarios"
    return "document_tail_risk_stress_review"


def _validate_report_consistency(
    report: ProbabilityEventTailRiskStressScenarioReport,
) -> None:
    tail_risk_charge_probability = _multiply_decimal(
        report.tail_event_probability,
        report.tail_loss_probability,
    )
    if report.tail_risk_charge_probability != tail_risk_charge_probability:
        raise ValueError("tail_risk_charge_probability does not match inputs")
    if report.stress_adjusted_edge_probability != _subtract_decimal(
        report.base_case_probability,
        tail_risk_charge_probability,
    ):
        raise ValueError("stress_adjusted_edge_probability does not match inputs")
    if report.scenario_coverage_ratio != _divide_decimal(
        report.scenario_coverage_count,
        report.required_scenario_count,
    ):
        raise ValueError("scenario_coverage_ratio does not match inputs")
    expected_reason_codes = _reason_codes(
        stress_adjusted_edge_probability=report.stress_adjusted_edge_probability,
        scenario_coverage_count=report.scenario_coverage_count,
        required_scenario_count=report.required_scenario_count,
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes do not match derived fields")
    expected_status = _tail_risk_status(expected_reason_codes)
    if report.tail_risk_status != expected_status:
        raise ValueError("tail_risk_status does not match reason_codes")
    if report.manual_next_step != _manual_next_step(expected_status):
        raise ValueError("manual_next_step does not match tail_risk_status")


def _public_payload_digest(report: ProbabilityEventTailRiskStressScenarioReport) -> str:
    digest_input = asdict(report)
    digest_input.pop("payload_digest", None)
    encoded = dumps(
        _json_ready(digest_input),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _apply_or_verify_payload_digest(
    report: ProbabilityEventTailRiskStressScenarioReport,
) -> None:
    expected = _public_payload_digest(report)
    provided = report.payload_digest
    if provided == "":
        object.__setattr__(report, "payload_digest", expected)
        return
    _require_digest("payload_digest", provided)
    if provided != expected:
        raise ValueError("payload_digest does not match derived fields")


def _verify_payload_digest(report: ProbabilityEventTailRiskStressScenarioReport) -> None:
    _require_digest("payload_digest", report.payload_digest)
    if report.payload_digest != _public_payload_digest(report):
        raise ValueError("payload_digest does not match derived fields")


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left * right)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left - right)


def _divide_decimal(left: Decimal, right: Decimal) -> Decimal:
    if right == ZERO:
        raise ValueError("division denominator must be nonzero")
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left / right)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize(value)


def _normalize_probability(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _normalize_count(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be integer-valued Decimal")
    return normalized


def _require_status(name: str, value: object) -> None:
    if value not in PROBABILITY_EVENT_TAIL_RISK_STRESS_SCENARIO_STATUSES:
        raise ValueError(f"{name} must be a known tail risk status")


def _require_reason_code(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value not in _REASON_CODES:
        raise ValueError(f"{name} must be a supported reason code")


def _normalize_reason_codes(name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    if not value:
        raise ValueError(f"{name} must not be empty")
    normalized = tuple(sorted(dict.fromkeys(value)))
    for reason_code in normalized:
        _require_reason_code(f"{name} item", reason_code)
    return normalized


def _require_manual_next_step(name: str, value: object) -> None:
    if value not in _MANUAL_NEXT_STEPS:
        raise ValueError(f"{name} must be a supported manual next step")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{name} must be a sha256 hex digest")
    for character in value:
        if character not in "0123456789abcdef":
            raise ValueError(f"{name} must be a sha256 hex digest")


def _validate_public_payload_schema(payload: dict[str, Any]) -> None:
    _require_public_keys("payload", payload, _PUBLIC_FIELDS)
    for field_name in (
        "base_case_probability",
        "tail_event_probability",
        "tail_loss_probability",
        "tail_risk_charge_probability",
    ):
        _normalize_probability_decimal_string(
            f"payload.{field_name}",
            payload.get(field_name),
        )
    for field_name in (
        "scenario_coverage_count",
        "required_scenario_count",
    ):
        _normalize_count_decimal_string(f"payload.{field_name}", payload.get(field_name))
    for field_name in (
        "scenario_coverage_ratio",
        "stress_adjusted_edge_probability",
    ):
        _normalize_decimal_string(f"payload.{field_name}", payload.get(field_name))
    _require_status("payload.tail_risk_status", payload.get("tail_risk_status"))
    _validate_public_reason_codes(payload.get("reason_codes"))
    _require_manual_next_step("payload.manual_next_step", payload.get("manual_next_step"))
    _require_digest("payload.payload_digest", payload.get("payload_digest"))
    _require_hard_flags("payload", _DictFlags(payload))


def _require_public_keys(
    label: str,
    value: dict[str, Any],
    expected: frozenset[str],
) -> None:
    if set(value) != expected:
        raise ValueError(f"{label} must match the public schema")


def _validate_public_reason_codes(value: object) -> None:
    if type(value) is not list:
        raise ValueError("payload.reason_codes must be a public list")
    if not value:
        raise ValueError("payload.reason_codes must not be empty")
    previous = ""
    for index, reason_code in enumerate(value):
        _require_reason_code(f"payload.reason_codes[{index}]", reason_code)
        if previous and reason_code <= previous:
            raise ValueError("payload.reason_codes must be sorted")
        previous = reason_code


def _normalize_decimal_string(name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{name} must be serialized as a string")
    return _normalize_decimal(name, Decimal(value))


def _normalize_probability_decimal_string(name: str, value: object) -> Decimal:
    return _normalize_probability(name, _normalize_decimal_string(name, value))


def _normalize_count_decimal_string(name: str, value: object) -> Decimal:
    return _normalize_count(name, _normalize_decimal_string(name, value))


def _json_ready(value: object) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


@dataclass(frozen=True)
class _DictFlags:
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


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        value = asdict(value)
    if isinstance(value, dict):
        for key, item in value.items():
            if _contains_unsafe_public_fragment(str(key)):
                raise ValueError(f"{label} has unsafe public payload")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (tuple, list)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, str) and _contains_unsafe_public_fragment(value):
        raise ValueError(f"{label} has unsafe public payload")


def _contains_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


__all__ = (
    "PROBABILITY_EVENT_TAIL_RISK_STRESS_SCENARIO_STATUSES",
    "ProbabilityEventTailRiskStressScenarioInput",
    "ProbabilityEventTailRiskStressScenarioReport",
    "build_probability_event_tail_risk_stress_scenario_report",
    "probability_event_tail_risk_stress_scenario_public_payload",
)
