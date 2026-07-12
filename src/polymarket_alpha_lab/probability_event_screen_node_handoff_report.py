"""Read-only node handoff readiness report for probability event screens."""

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
    "HANDOFF_BANDS",
    "ProbabilityEventScreenNodeHandoffInput",
    "ProbabilityEventScreenNodeHandoffReport",
    "build_probability_event_screen_node_handoff_report",
    "probability_event_screen_node_handoff_report_digest",
    "probability_event_screen_node_handoff_report_to_payload",
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
COMPONENT_COUNT = Decimal("8.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

HANDOFF_BANDS = ("ready", "attention", "blocked")

READY_REASON_CODE = "probability_event_screen_node_handoff_ready"
BLOCKED_REASON_SEQUENCE = (
    "node_handoff_end_to_end_not_ready",
    "node_handoff_system_health_not_ready",
    "node_handoff_validation_matrix_not_ready",
    "node_handoff_release_gate_not_ready",
    "node_handoff_operator_runbook_not_ready",
    "node_handoff_supabase_persistence_not_ready",
    "node_handoff_github_push_not_ready",
)
ATTENTION_REASON_SEQUENCE = (
    "node_handoff_learning_dashboard_not_ready",
    READY_REASON_CODE,
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
class ProbabilityEventScreenNodeHandoffInput(_FinalPublicDataclass):
    end_to_end_ready: bool
    system_health_ready: bool
    validation_matrix_ready: bool
    release_gate_ready: bool
    operator_runbook_ready: bool
    learning_dashboard_ready: bool
    supabase_persistence_ready: bool
    github_push_ready: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventScreenNodeHandoffInput,
            "node handoff input",
        )
        for field_name in _BOOL_INPUT_FIELDS:
            _require_bool(field_name, getattr(self, field_name))
        _require_hard_flags("node handoff input", self)


@dataclass(frozen=True)
class ProbabilityEventScreenNodeHandoffReport(_FinalPublicDataclass):
    end_to_end_ready: bool
    system_health_ready: bool
    validation_matrix_ready: bool
    release_gate_ready: bool
    operator_runbook_ready: bool
    learning_dashboard_ready: bool
    supabase_persistence_ready: bool
    github_push_ready: bool
    node_handoff_ready: bool
    handoff_band: str
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventScreenNodeHandoffReport,
            "node handoff report",
        )
        for field_name in _BOOL_INPUT_FIELDS + ("node_handoff_ready",):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "handoff_band",
            _normalize_member("handoff_band", self.handoff_band),
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
        _require_hard_flags("node handoff report", self)

    @property
    def public_payload(self) -> dict[str, object]:
        return probability_event_screen_node_handoff_report_to_payload(self)

    @property
    def digest(self) -> str:
        return probability_event_screen_node_handoff_report_digest(self)


_BOOL_INPUT_FIELDS = (
    "end_to_end_ready",
    "system_health_ready",
    "validation_matrix_ready",
    "release_gate_ready",
    "operator_runbook_ready",
    "learning_dashboard_ready",
    "supabase_persistence_ready",
    "github_push_ready",
)


def build_probability_event_screen_node_handoff_report(
    handoff_input: ProbabilityEventScreenNodeHandoffInput,
) -> ProbabilityEventScreenNodeHandoffReport:
    if type(handoff_input) is not ProbabilityEventScreenNodeHandoffInput:
        raise ValueError(
            "handoff_input must be a ProbabilityEventScreenNodeHandoffInput",
        )
    _require_hard_flags("node handoff input", handoff_input)

    blocked_reason_codes, attention_reason_codes, ready_component_count = (
        _handoff_findings(handoff_input)
    )
    handoff_band = _handoff_band(blocked_reason_codes, attention_reason_codes)

    return ProbabilityEventScreenNodeHandoffReport(
        end_to_end_ready=handoff_input.end_to_end_ready,
        system_health_ready=handoff_input.system_health_ready,
        validation_matrix_ready=handoff_input.validation_matrix_ready,
        release_gate_ready=handoff_input.release_gate_ready,
        operator_runbook_ready=handoff_input.operator_runbook_ready,
        learning_dashboard_ready=handoff_input.learning_dashboard_ready,
        supabase_persistence_ready=handoff_input.supabase_persistence_ready,
        github_push_ready=handoff_input.github_push_ready,
        node_handoff_ready=handoff_band == "ready",
        handoff_band=handoff_band,
        blocked_reason_codes=blocked_reason_codes,
        attention_reason_codes=attention_reason_codes,
        ready_ratio=_ratio(_count(ready_component_count), COMPONENT_COUNT),
        paper_only=handoff_input.paper_only,
        report_only=handoff_input.report_only,
        readonly=handoff_input.readonly,
    )


def probability_event_screen_node_handoff_report_to_payload(
    report: ProbabilityEventScreenNodeHandoffReport,
) -> dict[str, object]:
    if type(report) is not ProbabilityEventScreenNodeHandoffReport:
        raise ValueError("report must be a ProbabilityEventScreenNodeHandoffReport")
    _require_hard_flags("node handoff report", report)
    _validate_report(report)
    payload = json_ready_no_floats(
        {
            "end_to_end_ready": report.end_to_end_ready,
            "system_health_ready": report.system_health_ready,
            "validation_matrix_ready": report.validation_matrix_ready,
            "release_gate_ready": report.release_gate_ready,
            "operator_runbook_ready": report.operator_runbook_ready,
            "learning_dashboard_ready": report.learning_dashboard_ready,
            "supabase_persistence_ready": report.supabase_persistence_ready,
            "github_push_ready": report.github_push_ready,
            "node_handoff_ready": report.node_handoff_ready,
            "handoff_band": report.handoff_band,
            "blocked_reason_codes": report.blocked_reason_codes,
            "attention_reason_codes": report.attention_reason_codes,
            "ready_ratio": report.ready_ratio,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )
    reject_unsafe_surface_fields("probability event screen node handoff payload", payload)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def probability_event_screen_node_handoff_report_digest(
    report: ProbabilityEventScreenNodeHandoffReport,
) -> str:
    payload = probability_event_screen_node_handoff_report_to_payload(report)
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def _handoff_findings(
    handoff_input: ProbabilityEventScreenNodeHandoffInput,
) -> tuple[tuple[str, ...], tuple[str, ...], int]:
    blocked: list[str] = []
    ready_component_count = 0

    blocking_checks = (
        ("end_to_end_ready", "node_handoff_end_to_end_not_ready"),
        ("system_health_ready", "node_handoff_system_health_not_ready"),
        ("validation_matrix_ready", "node_handoff_validation_matrix_not_ready"),
        ("release_gate_ready", "node_handoff_release_gate_not_ready"),
        ("operator_runbook_ready", "node_handoff_operator_runbook_not_ready"),
        ("supabase_persistence_ready", "node_handoff_supabase_persistence_not_ready"),
        ("github_push_ready", "node_handoff_github_push_not_ready"),
    )
    for field_name, reason_code in blocking_checks:
        if getattr(handoff_input, field_name):
            ready_component_count += 1
        else:
            blocked.append(reason_code)

    attention: list[str] = []
    if handoff_input.learning_dashboard_ready:
        ready_component_count += 1
    else:
        attention.append("node_handoff_learning_dashboard_not_ready")

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


def _handoff_band(
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
    if value not in HANDOFF_BANDS:
        raise ValueError(f"{field_name} must be one of {HANDOFF_BANDS}")
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
            raise ValueError(f"{field_name} must contain known handoff codes")
        if reason_code in normalized:
            raise ValueError(f"{field_name} must be unique")
        normalized.append(reason_code)
    return tuple(reason for reason in allowed_values if reason in normalized)


def _validate_report(report: ProbabilityEventScreenNodeHandoffReport) -> None:
    handoff_input = ProbabilityEventScreenNodeHandoffInput(
        end_to_end_ready=report.end_to_end_ready,
        system_health_ready=report.system_health_ready,
        validation_matrix_ready=report.validation_matrix_ready,
        release_gate_ready=report.release_gate_ready,
        operator_runbook_ready=report.operator_runbook_ready,
        learning_dashboard_ready=report.learning_dashboard_ready,
        supabase_persistence_ready=report.supabase_persistence_ready,
        github_push_ready=report.github_push_ready,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    blocked_reason_codes, attention_reason_codes, ready_component_count = (
        _handoff_findings(handoff_input)
    )
    expected_band = _handoff_band(blocked_reason_codes, attention_reason_codes)
    if report.blocked_reason_codes != blocked_reason_codes:
        raise ValueError("blocked_reason_codes must match node handoff inputs")
    if report.attention_reason_codes != attention_reason_codes:
        raise ValueError("attention_reason_codes must match node handoff inputs")
    if report.handoff_band != expected_band:
        raise ValueError("handoff_band must match reason codes")
    if report.node_handoff_ready != (expected_band == "ready"):
        raise ValueError("node_handoff_ready must match handoff_band")
    expected_ready_ratio = _ratio(_count(ready_component_count), COMPONENT_COUNT)
    if report.ready_ratio != expected_ready_ratio:
        raise ValueError("ready_ratio must match node handoff inputs")


def _require_hard_flags(label: str, value: Any) -> None:
    require_paper_only_flags(label, value)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)
