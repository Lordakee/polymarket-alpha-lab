"""Read-only validation matrix report for probability event screen readiness."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


__all__ = (
    "PROBABILITY_EVENT_SCREEN_VALIDATION_MATRIX_BANDS",
    "ProbabilityEventScreenValidationMatrixInput",
    "ProbabilityEventScreenValidationMatrixReport",
    "build_probability_event_screen_validation_matrix_report",
    "probability_event_screen_validation_matrix_report_digest",
    "probability_event_screen_validation_matrix_report_to_payload",
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
COMPONENT_COUNT = Decimal("8.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

PROBABILITY_EVENT_SCREEN_VALIDATION_MATRIX_BANDS = (
    "ready",
    "attention",
    "blocked",
)

READY_REASON_CODE = "probability_event_screen_validation_matrix_ready"
BLOCKED_REASON_SEQUENCE = (
    "validation_matrix_focused_tests_not_ready",
    "validation_matrix_compile_not_ready",
    "validation_matrix_diff_check_not_ready",
    "validation_matrix_public_payload_safety_not_ready",
    "validation_matrix_supabase_contract_not_ready",
    "validation_matrix_operator_runbook_not_ready",
    "validation_matrix_release_gate_not_ready",
    "validation_matrix_system_health_not_ready",
)
ATTENTION_REASON_SEQUENCE = (
    "validation_matrix_operator_runbook_needs_attention",
    "validation_matrix_release_gate_needs_attention",
    "validation_matrix_system_health_needs_attention",
    READY_REASON_CODE,
)
BLOCKING_CHECKS = (
    "focused_tests_ready",
    "compile_ready",
    "diff_check_ready",
    "public_payload_safety_ready",
    "supabase_contract_ready",
)
ATTENTION_CHECKS = (
    "operator_runbook_ready",
    "release_gate_ready",
    "system_health_ready",
)
BLOCKED_REASON_BY_FIELD = {
    "focused_tests_ready": "validation_matrix_focused_tests_not_ready",
    "compile_ready": "validation_matrix_compile_not_ready",
    "diff_check_ready": "validation_matrix_diff_check_not_ready",
    "public_payload_safety_ready": (
        "validation_matrix_public_payload_safety_not_ready"
    ),
    "supabase_contract_ready": "validation_matrix_supabase_contract_not_ready",
    "operator_runbook_ready": "validation_matrix_operator_runbook_not_ready",
    "release_gate_ready": "validation_matrix_release_gate_not_ready",
    "system_health_ready": "validation_matrix_system_health_not_ready",
}
ATTENTION_REASON_BY_FIELD = {
    "operator_runbook_ready": "validation_matrix_operator_runbook_needs_attention",
    "release_gate_ready": "validation_matrix_release_gate_needs_attention",
    "system_health_ready": "validation_matrix_system_health_needs_attention",
}
_BOOL_INPUT_FIELDS = (
    "focused_tests_ready",
    "compile_ready",
    "diff_check_ready",
    "public_payload_safety_ready",
    "supabase_contract_ready",
    "operator_runbook_ready",
    "release_gate_ready",
    "system_health_ready",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ProbabilityEventScreenValidationMatrixInput(_FinalPublicDataclass):
    focused_tests_ready: bool
    compile_ready: bool
    diff_check_ready: bool
    public_payload_safety_ready: bool
    supabase_contract_ready: bool
    operator_runbook_ready: bool
    release_gate_ready: bool
    system_health_ready: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventScreenValidationMatrixInput,
            "validation matrix input",
        )
        for field_name in _BOOL_INPUT_FIELDS:
            _require_bool(field_name, getattr(self, field_name))
        _require_hard_flags("validation matrix input", self)


@dataclass(frozen=True)
class ProbabilityEventScreenValidationMatrixReport(_FinalPublicDataclass):
    focused_tests_ready: bool
    compile_ready: bool
    diff_check_ready: bool
    public_payload_safety_ready: bool
    supabase_contract_ready: bool
    operator_runbook_ready: bool
    release_gate_ready: bool
    system_health_ready: bool
    validation_matrix_ready: bool
    validation_band: str
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventScreenValidationMatrixReport,
            "validation matrix report",
        )
        for field_name in _BOOL_INPUT_FIELDS + ("validation_matrix_ready",):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "validation_band",
            _normalize_member("validation_band", self.validation_band),
        )
        object.__setattr__(
            self,
            "blocked_reason_codes",
            _normalize_reason_codes(
                "blocked_reason_codes",
                self.blocked_reason_codes,
                BLOCKED_REASON_SEQUENCE,
            ),
        )
        object.__setattr__(
            self,
            "attention_reason_codes",
            _normalize_reason_codes(
                "attention_reason_codes",
                self.attention_reason_codes,
                ATTENTION_REASON_SEQUENCE,
            ),
        )
        object.__setattr__(
            self,
            "ready_ratio",
            _normalize_ratio("ready_ratio", self.ready_ratio),
        )
        _validate_report(self)
        _require_hard_flags("validation matrix report", self)

    @property
    def public_payload(self) -> dict[str, object]:
        return probability_event_screen_validation_matrix_report_to_payload(self)

    @property
    def digest(self) -> str:
        return probability_event_screen_validation_matrix_report_digest(self)


def build_probability_event_screen_validation_matrix_report(
    validation_input: ProbabilityEventScreenValidationMatrixInput,
) -> ProbabilityEventScreenValidationMatrixReport:
    if type(validation_input) is not ProbabilityEventScreenValidationMatrixInput:
        raise ValueError(
            "validation_input must be a ProbabilityEventScreenValidationMatrixInput",
        )
    _require_hard_flags("validation matrix input", validation_input)
    blocked_reason_codes, attention_reason_codes, ready_component_count = (
        _validation_matrix_findings(validation_input)
    )
    validation_band = _validation_band(blocked_reason_codes, attention_reason_codes)

    return ProbabilityEventScreenValidationMatrixReport(
        focused_tests_ready=validation_input.focused_tests_ready,
        compile_ready=validation_input.compile_ready,
        diff_check_ready=validation_input.diff_check_ready,
        public_payload_safety_ready=validation_input.public_payload_safety_ready,
        supabase_contract_ready=validation_input.supabase_contract_ready,
        operator_runbook_ready=validation_input.operator_runbook_ready,
        release_gate_ready=validation_input.release_gate_ready,
        system_health_ready=validation_input.system_health_ready,
        validation_matrix_ready=validation_band == "ready",
        validation_band=validation_band,
        blocked_reason_codes=blocked_reason_codes,
        attention_reason_codes=attention_reason_codes,
        ready_ratio=_ratio(_count(ready_component_count), COMPONENT_COUNT),
        paper_only=validation_input.paper_only,
        report_only=validation_input.report_only,
        readonly=validation_input.readonly,
    )


def probability_event_screen_validation_matrix_report_to_payload(
    report: ProbabilityEventScreenValidationMatrixReport,
) -> dict[str, object]:
    if type(report) is not ProbabilityEventScreenValidationMatrixReport:
        raise ValueError("report must be a ProbabilityEventScreenValidationMatrixReport")
    _require_hard_flags("validation matrix report", report)
    _validate_report(report)
    payload = json_ready_no_floats(
        {
            "focused_tests_ready": report.focused_tests_ready,
            "compile_ready": report.compile_ready,
            "diff_check_ready": report.diff_check_ready,
            "public_payload_safety_ready": report.public_payload_safety_ready,
            "supabase_contract_ready": report.supabase_contract_ready,
            "operator_runbook_ready": report.operator_runbook_ready,
            "release_gate_ready": report.release_gate_ready,
            "system_health_ready": report.system_health_ready,
            "validation_matrix_ready": report.validation_matrix_ready,
            "validation_band": report.validation_band,
            "blocked_reason_codes": report.blocked_reason_codes,
            "attention_reason_codes": report.attention_reason_codes,
            "ready_ratio": report.ready_ratio,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )
    reject_unsafe_surface_fields("probability event screen validation matrix payload", payload)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def probability_event_screen_validation_matrix_report_digest(
    report: ProbabilityEventScreenValidationMatrixReport,
) -> str:
    payload = probability_event_screen_validation_matrix_report_to_payload(report)
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def _validation_matrix_findings(
    validation_input: ProbabilityEventScreenValidationMatrixInput,
) -> tuple[tuple[str, ...], tuple[str, ...], int]:
    blocked: list[str] = []
    attention: list[str] = []
    ready_component_count = 0

    for field_name in _BOOL_INPUT_FIELDS:
        if getattr(validation_input, field_name):
            ready_component_count += 1
        elif field_name in BLOCKING_CHECKS:
            blocked.append(BLOCKED_REASON_BY_FIELD[field_name])
        elif field_name in ATTENTION_CHECKS:
            attention.append(ATTENTION_REASON_BY_FIELD[field_name])

    if ready_component_count == 0:
        return BLOCKED_REASON_SEQUENCE, (), ready_component_count

    blocked_reason_codes = tuple(
        reason for reason in BLOCKED_REASON_SEQUENCE if reason in blocked
    )
    if blocked_reason_codes:
        return blocked_reason_codes, (), ready_component_count

    attention_reason_codes = tuple(
        reason for reason in ATTENTION_REASON_SEQUENCE if reason in attention
    )
    if not attention_reason_codes:
        attention_reason_codes = (READY_REASON_CODE,)
    return blocked_reason_codes, attention_reason_codes, ready_component_count


def _validation_band(
    blocked_reason_codes: tuple[str, ...],
    attention_reason_codes: tuple[str, ...],
) -> str:
    if blocked_reason_codes:
        return "blocked"
    if attention_reason_codes == (READY_REASON_CODE,):
        return "ready"
    return "attention"


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _normalize_member(field_name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a canonical string")
    if value.strip() != value or value.lower() != value:
        raise ValueError(f"{field_name} must be canonical lowercase text")
    if value not in PROBABILITY_EVENT_SCREEN_VALIDATION_MATRIX_BANDS:
        raise ValueError(
            f"{field_name} must be one of "
            f"{PROBABILITY_EVENT_SCREEN_VALIDATION_MATRIX_BANDS}",
        )
    return value


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for reason_code in value:
        if type(reason_code) is not str or not reason_code:
            raise ValueError(f"{field_name} must contain non-empty strings")
        if reason_code.strip() != reason_code or reason_code.lower() != reason_code:
            raise ValueError(f"{field_name} must contain canonical codes")
        if reason_code not in allowed_values:
            raise ValueError(f"{field_name} must contain known validation matrix codes")
        if reason_code in normalized:
            raise ValueError(f"{field_name} must be unique")
        normalized.append(reason_code)
    return tuple(reason for reason in allowed_values if reason in normalized)


def _validate_report(report: ProbabilityEventScreenValidationMatrixReport) -> None:
    validation_input = ProbabilityEventScreenValidationMatrixInput(
        focused_tests_ready=report.focused_tests_ready,
        compile_ready=report.compile_ready,
        diff_check_ready=report.diff_check_ready,
        public_payload_safety_ready=report.public_payload_safety_ready,
        supabase_contract_ready=report.supabase_contract_ready,
        operator_runbook_ready=report.operator_runbook_ready,
        release_gate_ready=report.release_gate_ready,
        system_health_ready=report.system_health_ready,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    blocked_reason_codes, attention_reason_codes, ready_component_count = (
        _validation_matrix_findings(validation_input)
    )
    expected_band = _validation_band(blocked_reason_codes, attention_reason_codes)
    if report.blocked_reason_codes != blocked_reason_codes:
        raise ValueError("blocked_reason_codes must match validation matrix inputs")
    if report.attention_reason_codes != attention_reason_codes:
        raise ValueError("attention_reason_codes must match validation matrix inputs")
    if report.validation_band != expected_band:
        raise ValueError("validation_band must match reason codes")
    if report.validation_matrix_ready != (expected_band == "ready"):
        raise ValueError("validation_matrix_ready must match validation_band")
    expected_ready_ratio = _ratio(_count(ready_component_count), COMPONENT_COUNT)
    if report.ready_ratio != expected_ready_ratio:
        raise ValueError("ready_ratio must match validation matrix inputs")


def _require_hard_flags(label: str, value: Any) -> None:
    require_paper_only_flags(label, value)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)
