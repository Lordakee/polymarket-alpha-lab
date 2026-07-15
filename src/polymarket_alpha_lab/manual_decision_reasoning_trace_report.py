"""Pure read-only manual decision reasoning trace readiness report."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "MANUAL_DECISION_REASONING_TRACE_DIGEST_FIELDS",
    "ManualDecisionReasoningTraceInput",
    "ManualDecisionReasoningTraceReport",
    "build_manual_decision_reasoning_trace_report",
    "manual_decision_reasoning_trace_report_digest",
    "manual_decision_reasoning_trace_report_payload",
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DIGEST_FIELD_COUNT = Decimal("7.000000")
TRACE_FIELD_COUNT = Decimal("8.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
MANUAL_DECISION_REASONING_TRACE_DIGEST_FIELDS = (
    "screen_digest_present",
    "research_digest_present",
    "source_reliability_digest_present",
    "cost_digest_present",
    "team_memory_digest_present",
    "position_sizing_digest_present",
    "operator_safety_digest_present",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ManualDecisionReasoningTraceInput(_FinalDataclass):
    screen_digest_present: Decimal
    research_digest_present: Decimal
    source_reliability_digest_present: Decimal
    cost_digest_present: Decimal
    team_memory_digest_present: Decimal
    position_sizing_digest_present: Decimal
    operator_safety_digest_present: Decimal
    decision_summary_redacted: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ManualDecisionReasoningTraceInput,
            "reasoning trace input",
        )
        for field_name in MANUAL_DECISION_REASONING_TRACE_DIGEST_FIELDS + (
            "decision_summary_redacted",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("reasoning trace input", self)


@dataclass(frozen=True)
class ManualDecisionReasoningTraceReport(_FinalDataclass):
    trace_ready: bool
    missing_digest_count: Decimal
    redaction_ready: bool
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ManualDecisionReasoningTraceReport,
            "reasoning trace report",
        )
        if type(self.trace_ready) is not bool:
            raise ValueError("trace_ready must be a bool")
        if type(self.redaction_ready) is not bool:
            raise ValueError("redaction_ready must be a bool")
        object.__setattr__(
            self,
            "missing_digest_count",
            _normalize_nonnegative_count(
                "missing_digest_count",
                self.missing_digest_count,
            ),
        )
        object.__setattr__(
            self,
            "blocked_reason_codes",
            _normalize_reason_codes("blocked_reason_codes", self.blocked_reason_codes),
        )
        object.__setattr__(
            self,
            "attention_reason_codes",
            _normalize_reason_codes(
                "attention_reason_codes",
                self.attention_reason_codes,
            ),
        )
        object.__setattr__(
            self,
            "ready_ratio",
            _normalize_ratio("ready_ratio", self.ready_ratio),
        )
        _validate_report(self)
        _require_hard_flags("reasoning trace report", self)

    @property
    def public_payload(self) -> dict[str, object]:
        return manual_decision_reasoning_trace_report_payload(self)

    @property
    def digest(self) -> str:
        return manual_decision_reasoning_trace_report_digest(self)


def build_manual_decision_reasoning_trace_report(
    trace_input: ManualDecisionReasoningTraceInput,
) -> ManualDecisionReasoningTraceReport:
    if type(trace_input) is not ManualDecisionReasoningTraceInput:
        raise ValueError("trace_input must be a ManualDecisionReasoningTraceInput")
    _require_hard_flags("reasoning trace input", trace_input)

    blocked_codes = tuple(
        f"manual_decision_reasoning_trace_{_digest_reason_name(field_name)}_missing"
        for field_name in MANUAL_DECISION_REASONING_TRACE_DIGEST_FIELDS
        if getattr(trace_input, field_name) == ZERO
    )
    attention_codes = tuple(
        f"manual_decision_reasoning_trace_{_digest_reason_name(field_name)}_attention"
        for field_name in MANUAL_DECISION_REASONING_TRACE_DIGEST_FIELDS
        if ZERO < getattr(trace_input, field_name) < ONE
    )
    redaction_ready = trace_input.decision_summary_redacted == ONE
    if not redaction_ready:
        blocked_codes += ("manual_decision_reasoning_trace_redaction_missing",)
    elif trace_input.decision_summary_redacted < ONE:
        attention_codes += ("manual_decision_reasoning_trace_redaction_attention",)

    if not blocked_codes and not attention_codes:
        attention_codes = ("manual_decision_reasoning_trace_ready",)

    digest_ready_count = sum(
        (
            _readiness_credit(getattr(trace_input, field_name))
            for field_name in MANUAL_DECISION_REASONING_TRACE_DIGEST_FIELDS
        ),
        ZERO,
    )
    redaction_ready_count = _readiness_credit(trace_input.decision_summary_redacted)

    return ManualDecisionReasoningTraceReport(
        trace_ready=not blocked_codes,
        missing_digest_count=_count(
            sum(
                1
                for field_name in MANUAL_DECISION_REASONING_TRACE_DIGEST_FIELDS
                if getattr(trace_input, field_name) == ZERO
            ),
        ),
        redaction_ready=redaction_ready,
        blocked_reason_codes=blocked_codes,
        attention_reason_codes=attention_codes,
        ready_ratio=_ratio(digest_ready_count + redaction_ready_count, TRACE_FIELD_COUNT),
        paper_only=trace_input.paper_only,
        report_only=trace_input.report_only,
        readonly=trace_input.readonly,
    )


def manual_decision_reasoning_trace_report_payload(
    report: ManualDecisionReasoningTraceReport,
) -> dict[str, object]:
    if type(report) is not ManualDecisionReasoningTraceReport:
        raise ValueError("report must be a ManualDecisionReasoningTraceReport")
    _require_hard_flags("reasoning trace report", report)
    _validate_report(report)
    return {
        "trace_ready": report.trace_ready,
        "missing_digest_count": _decimal_text(report.missing_digest_count),
        "redaction_ready": report.redaction_ready,
        "blocked_reason_codes": list(report.blocked_reason_codes),
        "attention_reason_codes": list(report.attention_reason_codes),
        "ready_ratio": _decimal_text(report.ready_ratio),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def manual_decision_reasoning_trace_report_digest(
    report: ManualDecisionReasoningTraceReport,
) -> str:
    payload = manual_decision_reasoning_trace_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(QUANTUM)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(QUANTUM)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer")
    return normalized


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for reason_code in value:
        if type(reason_code) is not str or not reason_code:
            raise ValueError(f"{field_name} must contain non-empty strings")
        if reason_code != reason_code.strip():
            raise ValueError(f"{field_name} must be stripped")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(normalized)


def _require_hard_flags(label: str, value: Any) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} must keep {field_name}=True")


def _validate_report(report: ManualDecisionReasoningTraceReport) -> None:
    if report.missing_digest_count > DIGEST_FIELD_COUNT:
        raise ValueError("missing_digest_count exceeds digest field count")
    if report.trace_ready == bool(report.blocked_reason_codes):
        if report.trace_ready:
            raise ValueError("ready reports must not include blocked_reason_codes")
        raise ValueError("blocked reports require blocked_reason_codes")
    if report.redaction_ready is not (
        "manual_decision_reasoning_trace_redaction_missing"
        not in report.blocked_reason_codes
    ):
        raise ValueError("redaction_ready must match redaction reason codes")
    if (
        report.attention_reason_codes
        == ("manual_decision_reasoning_trace_ready",)
        and (not report.trace_ready or report.ready_ratio != ONE)
    ):
        raise ValueError("ready reason requires trace_ready and ready_ratio=1.000000")


def _digest_reason_name(field_name: str) -> str:
    return field_name.removesuffix("_present")


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)


def _readiness_credit(value: Decimal) -> Decimal:
    if value == ONE:
        return ONE
    if value == ZERO:
        return ZERO
    return Decimal("0.500000")


def _decimal_text(value: Decimal) -> str:
    return format(value.quantize(QUANTUM), "f")
