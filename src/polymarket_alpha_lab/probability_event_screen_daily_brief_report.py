"""Read-only daily brief report for probability event screen meetings."""

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
    "ProbabilityEventScreenDailyBriefInput",
    "ProbabilityEventScreenDailyBriefReport",
    "build_probability_event_screen_daily_brief_report",
    "probability_event_screen_daily_brief_report_digest",
    "probability_event_screen_daily_brief_report_to_payload",
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
READY_RATIO_FLOOR = Decimal("0.500000")
SOURCE_RELIABILITY_WATCH_FLOOR = Decimal("0.700000")
SOURCE_RELIABILITY_BLOCK_FLOOR = Decimal("0.500000")
COST_BURDEN_WATCH_CEILING = Decimal("0.600000")
COST_BURDEN_BLOCK_CEILING = Decimal("0.800000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

HEADLINE_STATUSES = (
    "ready_for_manual_review",
    "attention_required",
    "blocked",
)
BLOCKED_REASON_SEQUENCE = (
    "probability_event_screen_daily_no_candidates",
    "probability_event_screen_daily_blocked_candidates_present",
    "probability_event_screen_daily_edge_below_threshold",
    "probability_event_screen_daily_source_reliability_block",
    "probability_event_screen_daily_cost_burden_block",
    "probability_event_screen_daily_no_high_priority_team",
    "probability_event_screen_daily_operator_safety_block",
)
ATTENTION_REASON_SEQUENCE = (
    "probability_event_screen_daily_ready_ratio_watch",
    "probability_event_screen_daily_watch_candidates_present",
    "probability_event_screen_daily_edge_at_threshold",
    "probability_event_screen_daily_source_reliability_watch",
    "probability_event_screen_daily_cost_burden_watch",
    "probability_event_screen_daily_operator_safety_watch",
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
class ProbabilityEventScreenDailyBriefInput(_FinalPublicDataclass):
    total_candidate_count: Decimal
    ready_for_manual_review_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_edge_to_threshold_probability: Decimal
    average_source_reliability_score: Decimal
    average_cost_burden_ratio: Decimal
    highest_priority_team_count: Decimal
    operator_safety_ready: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ProbabilityEventScreenDailyBriefInput, "brief input")
        for field_name in (
            "total_candidate_count",
            "ready_for_manual_review_count",
            "watch_count",
            "blocked_count",
            "highest_priority_team_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_edge_to_threshold_probability",
            _normalize_signed_probability(
                "average_edge_to_threshold_probability",
                self.average_edge_to_threshold_probability,
            ),
        )
        for field_name in (
            "average_source_reliability_score",
            "average_cost_burden_ratio",
            "operator_safety_ready",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _validate_input_counts(self)
        _require_hard_flags("brief input", self)


@dataclass(frozen=True)
class ProbabilityEventScreenDailyBriefReport(_FinalPublicDataclass):
    total_candidate_count: Decimal
    ready_for_manual_review_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_edge_to_threshold_probability: Decimal
    average_source_reliability_score: Decimal
    average_cost_burden_ratio: Decimal
    highest_priority_team_count: Decimal
    operator_safety_ready: Decimal
    daily_brief_ready: bool
    headline_status: str
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ProbabilityEventScreenDailyBriefReport, "brief report")
        for field_name in (
            "total_candidate_count",
            "ready_for_manual_review_count",
            "watch_count",
            "blocked_count",
            "highest_priority_team_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_edge_to_threshold_probability",
            _normalize_signed_probability(
                "average_edge_to_threshold_probability",
                self.average_edge_to_threshold_probability,
            ),
        )
        for field_name in (
            "average_source_reliability_score",
            "average_cost_burden_ratio",
            "operator_safety_ready",
            "ready_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "headline_status",
            _normalize_member("headline_status", self.headline_status, HEADLINE_STATUSES),
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
        if type(self.daily_brief_ready) is not bool:
            raise ValueError("daily_brief_ready must be a bool")
        _validate_report(self)
        _require_hard_flags("brief report", self)

    @property
    def public_payload(self) -> dict[str, object]:
        return probability_event_screen_daily_brief_report_to_payload(self)

    @property
    def digest(self) -> str:
        return probability_event_screen_daily_brief_report_digest(self)


def build_probability_event_screen_daily_brief_report(
    brief_input: ProbabilityEventScreenDailyBriefInput,
) -> ProbabilityEventScreenDailyBriefReport:
    if type(brief_input) is not ProbabilityEventScreenDailyBriefInput:
        raise ValueError("brief_input must be a ProbabilityEventScreenDailyBriefInput")
    _require_hard_flags("brief input", brief_input)

    ready_ratio = _ratio(
        brief_input.ready_for_manual_review_count,
        brief_input.total_candidate_count,
    )
    blocked_reason_codes, attention_reason_codes = _brief_reason_codes(
        brief_input,
        ready_ratio,
    )
    headline_status = _headline_status(blocked_reason_codes, attention_reason_codes)

    return ProbabilityEventScreenDailyBriefReport(
        total_candidate_count=brief_input.total_candidate_count,
        ready_for_manual_review_count=brief_input.ready_for_manual_review_count,
        watch_count=brief_input.watch_count,
        blocked_count=brief_input.blocked_count,
        average_edge_to_threshold_probability=(
            brief_input.average_edge_to_threshold_probability
        ),
        average_source_reliability_score=brief_input.average_source_reliability_score,
        average_cost_burden_ratio=brief_input.average_cost_burden_ratio,
        highest_priority_team_count=brief_input.highest_priority_team_count,
        operator_safety_ready=brief_input.operator_safety_ready,
        daily_brief_ready=headline_status == "ready_for_manual_review",
        headline_status=headline_status,
        blocked_reason_codes=blocked_reason_codes,
        attention_reason_codes=attention_reason_codes,
        ready_ratio=ready_ratio,
        paper_only=brief_input.paper_only,
        report_only=brief_input.report_only,
        readonly=brief_input.readonly,
    )


def probability_event_screen_daily_brief_report_to_payload(
    report: ProbabilityEventScreenDailyBriefReport,
) -> dict[str, object]:
    if type(report) is not ProbabilityEventScreenDailyBriefReport:
        raise ValueError("report must be a ProbabilityEventScreenDailyBriefReport")
    _require_hard_flags("brief report", report)
    _validate_report(report)
    payload = json_ready_no_floats(
        {
            "total_candidate_count": report.total_candidate_count,
            "ready_for_manual_review_count": report.ready_for_manual_review_count,
            "watch_count": report.watch_count,
            "blocked_count": report.blocked_count,
            "average_edge_to_threshold_probability": (
                report.average_edge_to_threshold_probability
            ),
            "average_source_reliability_score": report.average_source_reliability_score,
            "average_cost_burden_ratio": report.average_cost_burden_ratio,
            "highest_priority_team_count": report.highest_priority_team_count,
            "operator_safety_ready": report.operator_safety_ready,
            "daily_brief_ready": report.daily_brief_ready,
            "headline_status": report.headline_status,
            "blocked_reason_codes": report.blocked_reason_codes,
            "attention_reason_codes": report.attention_reason_codes,
            "ready_ratio": report.ready_ratio,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )
    reject_unsafe_surface_fields("probability event screen daily brief payload", payload)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def probability_event_screen_daily_brief_report_digest(
    report: ProbabilityEventScreenDailyBriefReport,
) -> str:
    payload = probability_event_screen_daily_brief_report_to_payload(report)
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def _brief_reason_codes(
    brief_input: ProbabilityEventScreenDailyBriefInput,
    ready_ratio: Decimal,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    blocked_reasons: list[str] = []
    attention_reasons: list[str] = []

    if brief_input.total_candidate_count == ZERO:
        blocked_reasons.append("probability_event_screen_daily_no_candidates")
    if brief_input.blocked_count > ZERO:
        blocked_reasons.append(
            "probability_event_screen_daily_blocked_candidates_present",
        )
    if ready_ratio < READY_RATIO_FLOOR:
        attention_reasons.append("probability_event_screen_daily_ready_ratio_watch")
    if brief_input.watch_count > ZERO:
        attention_reasons.append(
            "probability_event_screen_daily_watch_candidates_present",
        )
    if brief_input.average_edge_to_threshold_probability < ZERO:
        blocked_reasons.append("probability_event_screen_daily_edge_below_threshold")
    elif brief_input.average_edge_to_threshold_probability == ZERO:
        attention_reasons.append("probability_event_screen_daily_edge_at_threshold")
    if brief_input.average_source_reliability_score < SOURCE_RELIABILITY_BLOCK_FLOOR:
        blocked_reasons.append(
            "probability_event_screen_daily_source_reliability_block",
        )
    elif brief_input.average_source_reliability_score < SOURCE_RELIABILITY_WATCH_FLOOR:
        attention_reasons.append(
            "probability_event_screen_daily_source_reliability_watch",
        )
    if brief_input.average_cost_burden_ratio >= COST_BURDEN_BLOCK_CEILING:
        blocked_reasons.append("probability_event_screen_daily_cost_burden_block")
    elif brief_input.average_cost_burden_ratio >= COST_BURDEN_WATCH_CEILING:
        attention_reasons.append("probability_event_screen_daily_cost_burden_watch")
    if brief_input.highest_priority_team_count == ZERO:
        blocked_reasons.append("probability_event_screen_daily_no_high_priority_team")
    if brief_input.operator_safety_ready == ZERO:
        blocked_reasons.append("probability_event_screen_daily_operator_safety_block")
    elif brief_input.operator_safety_ready < ONE:
        attention_reasons.append("probability_event_screen_daily_operator_safety_watch")

    return (
        tuple(reason for reason in BLOCKED_REASON_SEQUENCE if reason in blocked_reasons),
        tuple(
            reason for reason in ATTENTION_REASON_SEQUENCE if reason in attention_reasons
        ),
    )


def _headline_status(
    blocked_reason_codes: tuple[str, ...],
    attention_reason_codes: tuple[str, ...],
) -> str:
    if blocked_reason_codes:
        return "blocked"
    if attention_reason_codes:
        only_watch_candidates = attention_reason_codes == (
            "probability_event_screen_daily_watch_candidates_present",
        )
        if only_watch_candidates:
            return "ready_for_manual_review"
        return "attention_required"
    return "ready_for_manual_review"


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


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
            raise ValueError(f"{field_name} must contain known daily brief codes")
        if reason_code in normalized:
            raise ValueError(f"{field_name} must be unique")
        normalized.append(reason_code)
    return tuple(reason for reason in allowed_values if reason in normalized)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_signed_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < -ONE or normalized > ONE:
        raise ValueError(f"{field_name} must be between -1.000000 and 1.000000")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _validate_input_counts(brief_input: ProbabilityEventScreenDailyBriefInput) -> None:
    if (
        brief_input.ready_for_manual_review_count
        + brief_input.watch_count
        + brief_input.blocked_count
    ) != brief_input.total_candidate_count:
        raise ValueError("candidate counts must sum to total_candidate_count")


def _validate_report(report: ProbabilityEventScreenDailyBriefReport) -> None:
    if (
        report.ready_for_manual_review_count + report.watch_count + report.blocked_count
    ) != report.total_candidate_count:
        raise ValueError("candidate counts must sum to total_candidate_count")
    expected_ready_ratio = _ratio(
        report.ready_for_manual_review_count,
        report.total_candidate_count,
    )
    if report.ready_ratio != expected_ready_ratio:
        raise ValueError("ready_ratio must match ready and total candidate counts")

    expected_blocked, expected_attention = _brief_reason_codes(
        ProbabilityEventScreenDailyBriefInput(
            total_candidate_count=report.total_candidate_count,
            ready_for_manual_review_count=report.ready_for_manual_review_count,
            watch_count=report.watch_count,
            blocked_count=report.blocked_count,
            average_edge_to_threshold_probability=(
                report.average_edge_to_threshold_probability
            ),
            average_source_reliability_score=report.average_source_reliability_score,
            average_cost_burden_ratio=report.average_cost_burden_ratio,
            highest_priority_team_count=report.highest_priority_team_count,
            operator_safety_ready=report.operator_safety_ready,
            paper_only=report.paper_only,
            report_only=report.report_only,
            readonly=report.readonly,
        ),
        report.ready_ratio,
    )
    if report.blocked_reason_codes != expected_blocked:
        raise ValueError("blocked_reason_codes must match daily brief inputs")
    if report.attention_reason_codes != expected_attention:
        raise ValueError("attention_reason_codes must match daily brief inputs")

    expected_headline = _headline_status(
        report.blocked_reason_codes,
        report.attention_reason_codes,
    )
    if report.headline_status != expected_headline:
        raise ValueError("headline_status must match reason codes")
    if report.daily_brief_ready != (expected_headline == "ready_for_manual_review"):
        raise ValueError("daily_brief_ready must match headline_status")


def _require_hard_flags(label: str, value: Any) -> None:
    require_paper_only_flags(label, value)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)
