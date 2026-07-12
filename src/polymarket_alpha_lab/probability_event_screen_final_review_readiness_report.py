"""Final manual review readiness report for probability event screens."""

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
    "FINAL_REVIEW_BANDS",
    "ProbabilityEventScreenFinalReviewReadinessInput",
    "ProbabilityEventScreenFinalReviewReadinessReport",
    "build_probability_event_screen_final_review_readiness_report",
    "probability_event_screen_final_review_readiness_report_digest",
    "probability_event_screen_final_review_readiness_report_to_payload",
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
COMPONENT_COUNT = Decimal("8.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

FINAL_REVIEW_BANDS = ("ready", "attention", "blocked")

READY_REASON_CODE = "probability_event_screen_final_review_ready"
BLOCKED_REASON_SEQUENCE = (
    "final_review_screen_contract_not_ready",
    "final_review_quality_index_not_ready",
    "final_review_decision_memo_not_ready",
    "final_review_go_no_go_not_ready",
    "final_review_review_packet_index_not_ready",
    "final_review_audit_summary_not_ready",
    "final_review_operating_review_not_ready",
)
ATTENTION_REASON_SEQUENCE = (
    "final_review_operator_public_output_not_safe",
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
class ProbabilityEventScreenFinalReviewReadinessInput(_FinalPublicDataclass):
    screen_contract_ready: bool
    quality_index_ready: bool
    decision_memo_ready: bool
    go_no_go_ready: bool
    review_packet_index_ready: bool
    audit_summary_ready: bool
    operating_review_ready: bool
    operator_public_output_safe: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventScreenFinalReviewReadinessInput,
            "final review input",
        )
        for field_name in _BOOL_INPUT_FIELDS:
            _require_bool(field_name, getattr(self, field_name))
        _require_hard_flags("final review input", self)


@dataclass(frozen=True)
class ProbabilityEventScreenFinalReviewReadinessReport(_FinalPublicDataclass):
    screen_contract_ready: bool
    quality_index_ready: bool
    decision_memo_ready: bool
    go_no_go_ready: bool
    review_packet_index_ready: bool
    audit_summary_ready: bool
    operating_review_ready: bool
    operator_public_output_safe: bool
    final_review_ready: bool
    final_review_band: str
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventScreenFinalReviewReadinessReport,
            "final review report",
        )
        for field_name in _BOOL_INPUT_FIELDS + ("final_review_ready",):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "final_review_band",
            _normalize_member("final_review_band", self.final_review_band),
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
        _require_hard_flags("final review report", self)

    @property
    def public_payload(self) -> dict[str, object]:
        return probability_event_screen_final_review_readiness_report_to_payload(self)

    @property
    def digest(self) -> str:
        return probability_event_screen_final_review_readiness_report_digest(self)


_BOOL_INPUT_FIELDS = (
    "screen_contract_ready",
    "quality_index_ready",
    "decision_memo_ready",
    "go_no_go_ready",
    "review_packet_index_ready",
    "audit_summary_ready",
    "operating_review_ready",
    "operator_public_output_safe",
)


def build_probability_event_screen_final_review_readiness_report(
    final_review_input: ProbabilityEventScreenFinalReviewReadinessInput,
) -> ProbabilityEventScreenFinalReviewReadinessReport:
    if type(final_review_input) is not ProbabilityEventScreenFinalReviewReadinessInput:
        raise ValueError(
            "final_review_input must be a ProbabilityEventScreenFinalReviewReadinessInput",
        )
    _require_hard_flags("final review input", final_review_input)

    blocked_reason_codes, attention_reason_codes, ready_component_count = (
        _final_review_findings(final_review_input)
    )
    final_review_band = _final_review_band(
        blocked_reason_codes,
        attention_reason_codes,
    )

    return ProbabilityEventScreenFinalReviewReadinessReport(
        screen_contract_ready=final_review_input.screen_contract_ready,
        quality_index_ready=final_review_input.quality_index_ready,
        decision_memo_ready=final_review_input.decision_memo_ready,
        go_no_go_ready=final_review_input.go_no_go_ready,
        review_packet_index_ready=final_review_input.review_packet_index_ready,
        audit_summary_ready=final_review_input.audit_summary_ready,
        operating_review_ready=final_review_input.operating_review_ready,
        operator_public_output_safe=final_review_input.operator_public_output_safe,
        final_review_ready=final_review_band == "ready",
        final_review_band=final_review_band,
        blocked_reason_codes=blocked_reason_codes,
        attention_reason_codes=attention_reason_codes,
        ready_ratio=_ratio(_count(ready_component_count), COMPONENT_COUNT),
        paper_only=final_review_input.paper_only,
        report_only=final_review_input.report_only,
        readonly=final_review_input.readonly,
    )


def probability_event_screen_final_review_readiness_report_to_payload(
    report: ProbabilityEventScreenFinalReviewReadinessReport,
) -> dict[str, object]:
    if type(report) is not ProbabilityEventScreenFinalReviewReadinessReport:
        raise ValueError(
            "report must be a ProbabilityEventScreenFinalReviewReadinessReport",
        )
    _require_hard_flags("final review report", report)
    _validate_report(report)
    payload = json_ready_no_floats(
        {
            "screen_contract_ready": report.screen_contract_ready,
            "quality_index_ready": report.quality_index_ready,
            "decision_memo_ready": report.decision_memo_ready,
            "go_no_go_ready": report.go_no_go_ready,
            "review_packet_index_ready": report.review_packet_index_ready,
            "audit_summary_ready": report.audit_summary_ready,
            "operating_review_ready": report.operating_review_ready,
            "operator_public_output_safe": report.operator_public_output_safe,
            "final_review_ready": report.final_review_ready,
            "final_review_band": report.final_review_band,
            "blocked_reason_codes": report.blocked_reason_codes,
            "attention_reason_codes": report.attention_reason_codes,
            "ready_ratio": report.ready_ratio,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )
    reject_unsafe_surface_fields("probability event screen final review payload", payload)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def probability_event_screen_final_review_readiness_report_digest(
    report: ProbabilityEventScreenFinalReviewReadinessReport,
) -> str:
    payload = probability_event_screen_final_review_readiness_report_to_payload(report)
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def _final_review_findings(
    final_review_input: ProbabilityEventScreenFinalReviewReadinessInput,
) -> tuple[tuple[str, ...], tuple[str, ...], int]:
    blocked: list[str] = []
    ready_component_count = 0

    readiness_checks = (
        ("screen_contract_ready", "final_review_screen_contract_not_ready"),
        ("quality_index_ready", "final_review_quality_index_not_ready"),
        ("decision_memo_ready", "final_review_decision_memo_not_ready"),
        ("go_no_go_ready", "final_review_go_no_go_not_ready"),
        (
            "review_packet_index_ready",
            "final_review_review_packet_index_not_ready",
        ),
        ("audit_summary_ready", "final_review_audit_summary_not_ready"),
        ("operating_review_ready", "final_review_operating_review_not_ready"),
    )
    for field_name, reason_code in readiness_checks:
        if getattr(final_review_input, field_name):
            ready_component_count += 1
        else:
            blocked.append(reason_code)

    attention: list[str] = []
    if final_review_input.operator_public_output_safe:
        ready_component_count += 1
    else:
        attention.append("final_review_operator_public_output_not_safe")

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


def _final_review_band(
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
    if value not in FINAL_REVIEW_BANDS:
        raise ValueError(f"{field_name} must be one of {FINAL_REVIEW_BANDS}")
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
            raise ValueError(f"{field_name} must contain known final review codes")
        if reason_code in normalized:
            raise ValueError(f"{field_name} must be unique")
        normalized.append(reason_code)
    return tuple(reason for reason in allowed_values if reason in normalized)


def _validate_report(report: ProbabilityEventScreenFinalReviewReadinessReport) -> None:
    final_review_input = ProbabilityEventScreenFinalReviewReadinessInput(
        screen_contract_ready=report.screen_contract_ready,
        quality_index_ready=report.quality_index_ready,
        decision_memo_ready=report.decision_memo_ready,
        go_no_go_ready=report.go_no_go_ready,
        review_packet_index_ready=report.review_packet_index_ready,
        audit_summary_ready=report.audit_summary_ready,
        operating_review_ready=report.operating_review_ready,
        operator_public_output_safe=report.operator_public_output_safe,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    blocked_reason_codes, attention_reason_codes, ready_component_count = (
        _final_review_findings(final_review_input)
    )
    expected_band = _final_review_band(blocked_reason_codes, attention_reason_codes)
    if report.blocked_reason_codes != blocked_reason_codes:
        raise ValueError("blocked_reason_codes must match final review inputs")
    if report.attention_reason_codes != attention_reason_codes:
        raise ValueError("attention_reason_codes must match final review inputs")
    if report.final_review_band != expected_band:
        raise ValueError("final_review_band must match reason codes")
    if report.final_review_ready != (expected_band == "ready"):
        raise ValueError("final_review_ready must match final_review_band")
    expected_ready_ratio = _ratio(_count(ready_component_count), COMPONENT_COUNT)
    if report.ready_ratio != expected_ready_ratio:
        raise ValueError("ready_ratio must match final review inputs")


def _require_hard_flags(label: str, value: Any) -> None:
    require_paper_only_flags(label, value)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)
