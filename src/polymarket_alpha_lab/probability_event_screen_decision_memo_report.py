"""Read-only readiness report for manual decision memo preparation."""

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
    "ProbabilityEventScreenDecisionMemoInput",
    "ProbabilityEventScreenDecisionMemoReport",
    "build_probability_event_screen_decision_memo_report",
    "probability_event_screen_decision_memo_report_digest",
    "probability_event_screen_decision_memo_report_to_payload",
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
COMPONENT_COUNT = Decimal("8.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

INFORMATION_GAP_BANDS = ("ready", "attention", "blocker")
MEMO_STATUS_BANDS = ("ready", "attention", "blocked")

READY_REASON_CODE = "probability_event_screen_decision_memo_ready"
BLOCKED_REASON_SEQUENCE = (
    "decision_memo_screen_digest_missing",
    "decision_memo_recommendation_digest_missing",
    "decision_memo_daily_brief_digest_missing",
    "decision_memo_due_diligence_depth_not_ready",
    "decision_memo_information_gap_blocker",
    "decision_memo_liquidity_exit_not_ready",
    "decision_memo_team_scorecard_not_ready",
    "decision_memo_operator_safety_not_ready",
)
ATTENTION_REASON_SEQUENCE = (
    "decision_memo_information_gap_attention",
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
class ProbabilityEventScreenDecisionMemoInput(_FinalPublicDataclass):
    screen_digest_present: bool
    recommendation_digest_present: bool
    daily_brief_digest_present: bool
    due_diligence_depth_ready: bool
    information_gap_band: str
    liquidity_exit_ready: bool
    team_scorecard_ready: bool
    operator_safety_ready: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ProbabilityEventScreenDecisionMemoInput, "memo input")
        for field_name in _BOOL_INPUT_FIELDS:
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "information_gap_band",
            _normalize_member(
                "information_gap_band",
                self.information_gap_band,
                INFORMATION_GAP_BANDS,
            ),
        )
        _require_hard_flags("memo input", self)


@dataclass(frozen=True)
class ProbabilityEventScreenDecisionMemoReport(_FinalPublicDataclass):
    screen_digest_present: bool
    recommendation_digest_present: bool
    daily_brief_digest_present: bool
    due_diligence_depth_ready: bool
    information_gap_band: str
    liquidity_exit_ready: bool
    team_scorecard_ready: bool
    operator_safety_ready: bool
    decision_memo_ready: bool
    memo_status_band: str
    missing_artifact_count: Decimal
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ProbabilityEventScreenDecisionMemoReport, "memo report")
        for field_name in _BOOL_INPUT_FIELDS + ("decision_memo_ready",):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "information_gap_band",
            _normalize_member(
                "information_gap_band",
                self.information_gap_band,
                INFORMATION_GAP_BANDS,
            ),
        )
        object.__setattr__(
            self,
            "memo_status_band",
            _normalize_member("memo_status_band", self.memo_status_band, MEMO_STATUS_BANDS),
        )
        object.__setattr__(
            self,
            "missing_artifact_count",
            _normalize_nonnegative_count(
                "missing_artifact_count",
                self.missing_artifact_count,
            ),
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
        _require_hard_flags("memo report", self)

    @property
    def public_payload(self) -> dict[str, object]:
        return probability_event_screen_decision_memo_report_to_payload(self)

    @property
    def digest(self) -> str:
        return probability_event_screen_decision_memo_report_digest(self)


_BOOL_INPUT_FIELDS = (
    "screen_digest_present",
    "recommendation_digest_present",
    "daily_brief_digest_present",
    "due_diligence_depth_ready",
    "liquidity_exit_ready",
    "team_scorecard_ready",
    "operator_safety_ready",
)


def build_probability_event_screen_decision_memo_report(
    memo_input: ProbabilityEventScreenDecisionMemoInput,
) -> ProbabilityEventScreenDecisionMemoReport:
    if type(memo_input) is not ProbabilityEventScreenDecisionMemoInput:
        raise ValueError("memo_input must be a ProbabilityEventScreenDecisionMemoInput")
    _require_hard_flags("memo input", memo_input)

    blocked_reason_codes, attention_reason_codes, ready_component_count = _memo_findings(
        memo_input,
    )
    memo_status_band = _memo_status_band(blocked_reason_codes, attention_reason_codes)

    return ProbabilityEventScreenDecisionMemoReport(
        screen_digest_present=memo_input.screen_digest_present,
        recommendation_digest_present=memo_input.recommendation_digest_present,
        daily_brief_digest_present=memo_input.daily_brief_digest_present,
        due_diligence_depth_ready=memo_input.due_diligence_depth_ready,
        information_gap_band=memo_input.information_gap_band,
        liquidity_exit_ready=memo_input.liquidity_exit_ready,
        team_scorecard_ready=memo_input.team_scorecard_ready,
        operator_safety_ready=memo_input.operator_safety_ready,
        decision_memo_ready=memo_status_band == "ready",
        memo_status_band=memo_status_band,
        missing_artifact_count=_count(len(blocked_reason_codes)),
        blocked_reason_codes=blocked_reason_codes,
        attention_reason_codes=attention_reason_codes,
        ready_ratio=_ratio(_count(ready_component_count), COMPONENT_COUNT),
        paper_only=memo_input.paper_only,
        report_only=memo_input.report_only,
        readonly=memo_input.readonly,
    )


def probability_event_screen_decision_memo_report_to_payload(
    report: ProbabilityEventScreenDecisionMemoReport,
) -> dict[str, object]:
    if type(report) is not ProbabilityEventScreenDecisionMemoReport:
        raise ValueError("report must be a ProbabilityEventScreenDecisionMemoReport")
    _require_hard_flags("memo report", report)
    _validate_report(report)
    payload = json_ready_no_floats(
        {
            "screen_digest_present": report.screen_digest_present,
            "recommendation_digest_present": report.recommendation_digest_present,
            "daily_brief_digest_present": report.daily_brief_digest_present,
            "due_diligence_depth_ready": report.due_diligence_depth_ready,
            "information_gap_band": report.information_gap_band,
            "liquidity_exit_ready": report.liquidity_exit_ready,
            "team_scorecard_ready": report.team_scorecard_ready,
            "operator_safety_ready": report.operator_safety_ready,
            "decision_memo_ready": report.decision_memo_ready,
            "memo_status_band": report.memo_status_band,
            "missing_artifact_count": report.missing_artifact_count,
            "blocked_reason_codes": report.blocked_reason_codes,
            "attention_reason_codes": report.attention_reason_codes,
            "ready_ratio": report.ready_ratio,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )
    reject_unsafe_surface_fields("probability event screen decision memo payload", payload)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def probability_event_screen_decision_memo_report_digest(
    report: ProbabilityEventScreenDecisionMemoReport,
) -> str:
    payload = probability_event_screen_decision_memo_report_to_payload(report)
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def _memo_findings(
    memo_input: ProbabilityEventScreenDecisionMemoInput,
) -> tuple[tuple[str, ...], tuple[str, ...], int]:
    blocked: list[str] = []
    ready_component_count = 0

    readiness_checks = (
        ("screen_digest_present", "decision_memo_screen_digest_missing"),
        (
            "recommendation_digest_present",
            "decision_memo_recommendation_digest_missing",
        ),
        ("daily_brief_digest_present", "decision_memo_daily_brief_digest_missing"),
        (
            "due_diligence_depth_ready",
            "decision_memo_due_diligence_depth_not_ready",
        ),
        ("liquidity_exit_ready", "decision_memo_liquidity_exit_not_ready"),
        ("team_scorecard_ready", "decision_memo_team_scorecard_not_ready"),
        ("operator_safety_ready", "decision_memo_operator_safety_not_ready"),
    )
    for field_name, reason_code in readiness_checks:
        if getattr(memo_input, field_name):
            ready_component_count += 1
        else:
            blocked.append(reason_code)

    attention: list[str] = []
    if memo_input.information_gap_band == "ready":
        ready_component_count += 1
    elif memo_input.information_gap_band == "attention":
        attention.append("decision_memo_information_gap_attention")
    else:
        blocked.append("decision_memo_information_gap_blocker")

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


def _memo_status_band(
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


def _normalize_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a canonical string")
    if value.strip() != value or value.lower() != value:
        raise ValueError(f"{field_name} must be canonical lowercase text")
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")
    return value


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


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
            raise ValueError(f"{field_name} must contain known decision memo codes")
        if reason_code in normalized:
            raise ValueError(f"{field_name} must be unique")
        normalized.append(reason_code)
    return tuple(reason for reason in allowed_values if reason in normalized)


def _validate_report(report: ProbabilityEventScreenDecisionMemoReport) -> None:
    memo_input = ProbabilityEventScreenDecisionMemoInput(
        screen_digest_present=report.screen_digest_present,
        recommendation_digest_present=report.recommendation_digest_present,
        daily_brief_digest_present=report.daily_brief_digest_present,
        due_diligence_depth_ready=report.due_diligence_depth_ready,
        information_gap_band=report.information_gap_band,
        liquidity_exit_ready=report.liquidity_exit_ready,
        team_scorecard_ready=report.team_scorecard_ready,
        operator_safety_ready=report.operator_safety_ready,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    blocked_reason_codes, attention_reason_codes, ready_component_count = _memo_findings(
        memo_input,
    )
    expected_status_band = _memo_status_band(blocked_reason_codes, attention_reason_codes)
    if report.blocked_reason_codes != blocked_reason_codes:
        raise ValueError("blocked_reason_codes must match memo inputs")
    if report.attention_reason_codes != attention_reason_codes:
        raise ValueError("attention_reason_codes must match memo inputs")
    if report.memo_status_band != expected_status_band:
        raise ValueError("memo_status_band must match reason codes")
    if report.decision_memo_ready != (expected_status_band == "ready"):
        raise ValueError("decision_memo_ready must match memo_status_band")
    if report.missing_artifact_count != _count(len(blocked_reason_codes)):
        raise ValueError("missing_artifact_count must match blocked reason codes")
    expected_ready_ratio = _ratio(_count(ready_component_count), COMPONENT_COUNT)
    if report.ready_ratio != expected_ready_ratio:
        raise ValueError("ready_ratio must match memo inputs")


def _require_hard_flags(label: str, value: Any) -> None:
    require_paper_only_flags(label, value)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)
