"""Read-only release gate report for probability event screen development."""

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
    "ProbabilityEventScreenReleaseGateInput",
    "ProbabilityEventScreenReleaseGateReport",
    "RELEASE_GATE_BANDS",
    "build_probability_event_screen_release_gate_report",
    "probability_event_screen_release_gate_report_digest",
    "probability_event_screen_release_gate_report_to_payload",
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
COMPONENT_COUNT = Decimal("8.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

RELEASE_GATE_BANDS = ("ready", "attention", "blocked")

READY_REASON_CODE = "probability_event_screen_release_gate_ready"
BLOCKED_REASON_SEQUENCE = (
    "release_gate_commit_readiness_not_ready",
    "release_gate_final_review_not_ready",
    "release_gate_operator_runbook_not_ready",
    "release_gate_dashboard_snapshot_not_ready",
    "release_gate_audit_summary_not_ready",
    "release_gate_codegraph_sync_not_ready",
    "release_gate_claude_review_not_ready",
)
ATTENTION_REASON_SEQUENCE = (
    "release_gate_live_execution_surface_detected",
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
class ProbabilityEventScreenReleaseGateInput(_FinalPublicDataclass):
    commit_readiness_ready: bool
    final_review_ready: bool
    operator_runbook_ready: bool
    dashboard_snapshot_ready: bool
    audit_summary_ready: bool
    codegraph_sync_ready: bool
    claude_review_ready: bool
    no_live_execution_surface: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventScreenReleaseGateInput,
            "release gate input",
        )
        for field_name in _BOOL_INPUT_FIELDS:
            _require_bool(field_name, getattr(self, field_name))
        _require_hard_flags("release gate input", self)


@dataclass(frozen=True)
class ProbabilityEventScreenReleaseGateReport(_FinalPublicDataclass):
    commit_readiness_ready: bool
    final_review_ready: bool
    operator_runbook_ready: bool
    dashboard_snapshot_ready: bool
    audit_summary_ready: bool
    codegraph_sync_ready: bool
    claude_review_ready: bool
    no_live_execution_surface: bool
    release_gate_ready: bool
    release_gate_band: str
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventScreenReleaseGateReport,
            "release gate report",
        )
        for field_name in _BOOL_INPUT_FIELDS + ("release_gate_ready",):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "release_gate_band",
            _normalize_member("release_gate_band", self.release_gate_band),
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
        _require_hard_flags("release gate report", self)

    @property
    def public_payload(self) -> dict[str, object]:
        return probability_event_screen_release_gate_report_to_payload(self)

    @property
    def digest(self) -> str:
        return probability_event_screen_release_gate_report_digest(self)


_BOOL_INPUT_FIELDS = (
    "commit_readiness_ready",
    "final_review_ready",
    "operator_runbook_ready",
    "dashboard_snapshot_ready",
    "audit_summary_ready",
    "codegraph_sync_ready",
    "claude_review_ready",
    "no_live_execution_surface",
)


def build_probability_event_screen_release_gate_report(
    release_gate_input: ProbabilityEventScreenReleaseGateInput,
) -> ProbabilityEventScreenReleaseGateReport:
    if type(release_gate_input) is not ProbabilityEventScreenReleaseGateInput:
        raise ValueError(
            "release_gate_input must be a ProbabilityEventScreenReleaseGateInput",
        )
    _require_hard_flags("release gate input", release_gate_input)

    blocked_reason_codes, attention_reason_codes, ready_component_count = (
        _release_gate_findings(release_gate_input)
    )
    release_gate_band = _release_gate_band(
        blocked_reason_codes,
        attention_reason_codes,
    )

    return ProbabilityEventScreenReleaseGateReport(
        commit_readiness_ready=release_gate_input.commit_readiness_ready,
        final_review_ready=release_gate_input.final_review_ready,
        operator_runbook_ready=release_gate_input.operator_runbook_ready,
        dashboard_snapshot_ready=release_gate_input.dashboard_snapshot_ready,
        audit_summary_ready=release_gate_input.audit_summary_ready,
        codegraph_sync_ready=release_gate_input.codegraph_sync_ready,
        claude_review_ready=release_gate_input.claude_review_ready,
        no_live_execution_surface=release_gate_input.no_live_execution_surface,
        release_gate_ready=release_gate_band == "ready",
        release_gate_band=release_gate_band,
        blocked_reason_codes=blocked_reason_codes,
        attention_reason_codes=attention_reason_codes,
        ready_ratio=_ratio(_count(ready_component_count), COMPONENT_COUNT),
        paper_only=release_gate_input.paper_only,
        report_only=release_gate_input.report_only,
        readonly=release_gate_input.readonly,
    )


def probability_event_screen_release_gate_report_to_payload(
    report: ProbabilityEventScreenReleaseGateReport,
) -> dict[str, object]:
    if type(report) is not ProbabilityEventScreenReleaseGateReport:
        raise ValueError("report must be a ProbabilityEventScreenReleaseGateReport")
    _require_hard_flags("release gate report", report)
    _validate_report(report)
    payload = json_ready_no_floats(
        {
            "commit_readiness_ready": report.commit_readiness_ready,
            "final_review_ready": report.final_review_ready,
            "operator_runbook_ready": report.operator_runbook_ready,
            "dashboard_snapshot_ready": report.dashboard_snapshot_ready,
            "audit_summary_ready": report.audit_summary_ready,
            "codegraph_sync_ready": report.codegraph_sync_ready,
            "claude_review_ready": report.claude_review_ready,
            "no_live_execution_surface": report.no_live_execution_surface,
            "release_gate_ready": report.release_gate_ready,
            "release_gate_band": report.release_gate_band,
            "blocked_reason_codes": report.blocked_reason_codes,
            "attention_reason_codes": report.attention_reason_codes,
            "ready_ratio": report.ready_ratio,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )
    reject_unsafe_surface_fields("probability event screen release gate payload", payload)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def probability_event_screen_release_gate_report_digest(
    report: ProbabilityEventScreenReleaseGateReport,
) -> str:
    payload = probability_event_screen_release_gate_report_to_payload(report)
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def _release_gate_findings(
    release_gate_input: ProbabilityEventScreenReleaseGateInput,
) -> tuple[tuple[str, ...], tuple[str, ...], int]:
    blocked: list[str] = []
    ready_component_count = 0

    readiness_checks = (
        ("commit_readiness_ready", "release_gate_commit_readiness_not_ready"),
        ("final_review_ready", "release_gate_final_review_not_ready"),
        ("operator_runbook_ready", "release_gate_operator_runbook_not_ready"),
        ("dashboard_snapshot_ready", "release_gate_dashboard_snapshot_not_ready"),
        ("audit_summary_ready", "release_gate_audit_summary_not_ready"),
        ("codegraph_sync_ready", "release_gate_codegraph_sync_not_ready"),
        ("claude_review_ready", "release_gate_claude_review_not_ready"),
    )
    for field_name, reason_code in readiness_checks:
        if getattr(release_gate_input, field_name):
            ready_component_count += 1
        else:
            blocked.append(reason_code)

    attention: list[str] = []
    if release_gate_input.no_live_execution_surface:
        ready_component_count += 1
    else:
        attention.append("release_gate_live_execution_surface_detected")

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


def _release_gate_band(
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
    if value not in RELEASE_GATE_BANDS:
        raise ValueError(f"{field_name} must be one of {RELEASE_GATE_BANDS}")
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
            raise ValueError(f"{field_name} must contain known release gate codes")
        if reason_code in normalized:
            raise ValueError(f"{field_name} must be unique")
        normalized.append(reason_code)
    return tuple(reason for reason in allowed_values if reason in normalized)


def _validate_report(report: ProbabilityEventScreenReleaseGateReport) -> None:
    release_gate_input = ProbabilityEventScreenReleaseGateInput(
        commit_readiness_ready=report.commit_readiness_ready,
        final_review_ready=report.final_review_ready,
        operator_runbook_ready=report.operator_runbook_ready,
        dashboard_snapshot_ready=report.dashboard_snapshot_ready,
        audit_summary_ready=report.audit_summary_ready,
        codegraph_sync_ready=report.codegraph_sync_ready,
        claude_review_ready=report.claude_review_ready,
        no_live_execution_surface=report.no_live_execution_surface,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    blocked_reason_codes, attention_reason_codes, ready_component_count = (
        _release_gate_findings(release_gate_input)
    )
    expected_band = _release_gate_band(blocked_reason_codes, attention_reason_codes)
    if report.blocked_reason_codes != blocked_reason_codes:
        raise ValueError("blocked_reason_codes must match release gate inputs")
    if report.attention_reason_codes != attention_reason_codes:
        raise ValueError("attention_reason_codes must match release gate inputs")
    if report.release_gate_band != expected_band:
        raise ValueError("release_gate_band must match reason codes")
    if report.release_gate_ready != (expected_band == "ready"):
        raise ValueError("release_gate_ready must match release_gate_band")
    expected_ready_ratio = _ratio(_count(ready_component_count), COMPONENT_COUNT)
    if report.ready_ratio != expected_ready_ratio:
        raise ValueError("ready_ratio must match release gate inputs")


def _require_hard_flags(label: str, value: Any) -> None:
    require_paper_only_flags(label, value)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)
