"""Read-only recommendation report for ProbabilityEventScreen outputs."""

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
    "PROBABILITY_EVENT_SCREEN_COMPONENT_FIELDS",
    "ProbabilityEventScreenRecommendationInput",
    "ProbabilityEventScreenRecommendationReport",
    "build_probability_event_screen_recommendation_report",
    "probability_event_screen_recommendation_report_digest",
    "probability_event_screen_recommendation_report_to_payload",
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
COMPONENT_COUNT = Decimal("8.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

PROBABILITY_EVENT_SCREEN_COMPONENT_FIELDS = (
    "screen_status",
    "edge_to_threshold_probability",
    "source_quality_status",
    "team_route_confidence",
    "memory_context_ready",
    "position_sizing_risk_band",
    "preflight_ready",
    "operator_safety_ready",
)
SCREEN_STATUSES = ("ready_for_manual_review", "ready", "watch", "block")
SOURCE_QUALITY_STATUSES = ("ready", "watch", "block")
POSITION_SIZING_RISK_BANDS = ("low", "medium", "high", "block", "blocked")
RECOMMENDATION_BANDS = ("ready_for_manual_review", "watch", "block")
READY_REASON_CODE = "probability_event_screen_ready_for_manual_review"


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
class ProbabilityEventScreenRecommendationInput(_FinalPublicDataclass):
    screen_status: str
    edge_to_threshold_probability: Decimal
    source_quality_status: str
    team_route_confidence: Decimal
    memory_context_ready: Decimal
    position_sizing_risk_band: str
    preflight_ready: Decimal
    operator_safety_ready: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventScreenRecommendationInput,
            "screen input",
        )
        object.__setattr__(
            self,
            "screen_status",
            _normalize_member("screen_status", self.screen_status, SCREEN_STATUSES),
        )
        object.__setattr__(
            self,
            "edge_to_threshold_probability",
            _normalize_signed_probability(
                "edge_to_threshold_probability",
                self.edge_to_threshold_probability,
            ),
        )
        object.__setattr__(
            self,
            "source_quality_status",
            _normalize_member(
                "source_quality_status",
                self.source_quality_status,
                SOURCE_QUALITY_STATUSES,
            ),
        )
        for field_name in (
            "team_route_confidence",
            "memory_context_ready",
            "preflight_ready",
            "operator_safety_ready",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "position_sizing_risk_band",
            _normalize_member(
                "position_sizing_risk_band",
                self.position_sizing_risk_band,
                POSITION_SIZING_RISK_BANDS,
            ),
        )
        _require_hard_flags("screen input", self)


@dataclass(frozen=True)
class ProbabilityEventScreenRecommendationReport(_FinalPublicDataclass):
    screen_status: str
    edge_to_threshold_probability: Decimal
    source_quality_status: str
    team_route_confidence: Decimal
    memory_context_ready: Decimal
    position_sizing_risk_band: str
    preflight_ready: Decimal
    operator_safety_ready: Decimal
    recommendation_band: str
    primary_reason_codes: tuple[str, ...]
    blocker_count: Decimal
    attention_count: Decimal
    ready_component_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventScreenRecommendationReport,
            "recommendation report",
        )
        object.__setattr__(
            self,
            "screen_status",
            _normalize_member("screen_status", self.screen_status, SCREEN_STATUSES),
        )
        object.__setattr__(
            self,
            "edge_to_threshold_probability",
            _normalize_signed_probability(
                "edge_to_threshold_probability",
                self.edge_to_threshold_probability,
            ),
        )
        object.__setattr__(
            self,
            "source_quality_status",
            _normalize_member(
                "source_quality_status",
                self.source_quality_status,
                SOURCE_QUALITY_STATUSES,
            ),
        )
        for field_name in (
            "team_route_confidence",
            "memory_context_ready",
            "preflight_ready",
            "operator_safety_ready",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "position_sizing_risk_band",
            _normalize_member(
                "position_sizing_risk_band",
                self.position_sizing_risk_band,
                POSITION_SIZING_RISK_BANDS,
            ),
        )
        object.__setattr__(
            self,
            "recommendation_band",
            _normalize_member(
                "recommendation_band",
                self.recommendation_band,
                RECOMMENDATION_BANDS,
            ),
        )
        object.__setattr__(
            self,
            "primary_reason_codes",
            _normalize_reason_codes(self.primary_reason_codes),
        )
        for field_name in ("blocker_count", "attention_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "ready_component_ratio",
            _normalize_ratio("ready_component_ratio", self.ready_component_ratio),
        )
        _validate_report(self)
        _require_hard_flags("recommendation report", self)

    @property
    def public_payload(self) -> dict[str, object]:
        return probability_event_screen_recommendation_report_to_payload(self)

    @property
    def digest(self) -> str:
        return probability_event_screen_recommendation_report_digest(self)


def build_probability_event_screen_recommendation_report(
    screen: ProbabilityEventScreenRecommendationInput,
) -> ProbabilityEventScreenRecommendationReport:
    if type(screen) is not ProbabilityEventScreenRecommendationInput:
        raise ValueError("screen must be a ProbabilityEventScreenRecommendationInput")
    _require_hard_flags("screen input", screen)

    blocker_codes, attention_codes, ready_component_count = _component_findings(screen)
    blocker_count = _count(len(blocker_codes))
    attention_count = _count(len(attention_codes))
    reason_codes = blocker_codes + attention_codes
    if not reason_codes:
        reason_codes = (READY_REASON_CODE,)

    return ProbabilityEventScreenRecommendationReport(
        screen_status=screen.screen_status,
        edge_to_threshold_probability=screen.edge_to_threshold_probability,
        source_quality_status=screen.source_quality_status,
        team_route_confidence=screen.team_route_confidence,
        memory_context_ready=screen.memory_context_ready,
        position_sizing_risk_band=screen.position_sizing_risk_band,
        preflight_ready=screen.preflight_ready,
        operator_safety_ready=screen.operator_safety_ready,
        recommendation_band=_recommendation_band(blocker_count, attention_count),
        primary_reason_codes=reason_codes,
        blocker_count=blocker_count,
        attention_count=attention_count,
        ready_component_ratio=_ratio(_count(ready_component_count), COMPONENT_COUNT),
        paper_only=screen.paper_only,
        report_only=screen.report_only,
        readonly=screen.readonly,
    )


def probability_event_screen_recommendation_report_to_payload(
    report: ProbabilityEventScreenRecommendationReport,
) -> dict[str, object]:
    if type(report) is not ProbabilityEventScreenRecommendationReport:
        raise ValueError("report must be a ProbabilityEventScreenRecommendationReport")
    _require_hard_flags("recommendation report", report)
    _validate_report(report)
    payload = json_ready_no_floats(
        {
            "screen_status": report.screen_status,
            "edge_to_threshold_probability": report.edge_to_threshold_probability,
            "source_quality_status": report.source_quality_status,
            "team_route_confidence": report.team_route_confidence,
            "memory_context_ready": report.memory_context_ready,
            "position_sizing_risk_band": report.position_sizing_risk_band,
            "preflight_ready": report.preflight_ready,
            "operator_safety_ready": report.operator_safety_ready,
            "recommendation_band": report.recommendation_band,
            "primary_reason_codes": report.primary_reason_codes,
            "blocker_count": report.blocker_count,
            "attention_count": report.attention_count,
            "ready_component_ratio": report.ready_component_ratio,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )
    reject_unsafe_surface_fields("probability event screen recommendation payload", payload)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def probability_event_screen_recommendation_report_digest(
    report: ProbabilityEventScreenRecommendationReport,
) -> str:
    payload = probability_event_screen_recommendation_report_to_payload(report)
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def _component_findings(
    screen: ProbabilityEventScreenRecommendationInput,
) -> tuple[tuple[str, ...], tuple[str, ...], int]:
    blocker_codes: list[str] = []
    attention_codes: list[str] = []
    ready_component_count = 0

    if screen.screen_status == "block":
        blocker_codes.append("probability_event_screen_status_block")
    elif screen.screen_status == "watch":
        attention_codes.append("probability_event_screen_status_watch")
    else:
        ready_component_count += 1

    if screen.edge_to_threshold_probability < ZERO:
        blocker_codes.append("probability_event_edge_below_threshold_block")
    elif screen.edge_to_threshold_probability == ZERO:
        attention_codes.append("probability_event_edge_at_threshold_watch")
    else:
        ready_component_count += 1

    if screen.source_quality_status == "block":
        blocker_codes.append("probability_event_source_quality_block")
    elif screen.source_quality_status == "watch":
        attention_codes.append("probability_event_source_quality_watch")
    else:
        ready_component_count += 1

    ready_component_count += _ratio_component_findings(
        "team_route_confidence",
        screen.team_route_confidence,
        blocker_codes,
        attention_codes,
    )
    ready_component_count += _ratio_component_findings(
        "memory_context",
        screen.memory_context_ready,
        blocker_codes,
        attention_codes,
    )

    if screen.position_sizing_risk_band in ("high", "block", "blocked"):
        blocker_codes.append("probability_event_position_sizing_risk_block")
    elif screen.position_sizing_risk_band == "medium":
        attention_codes.append("probability_event_position_sizing_risk_watch")
    else:
        ready_component_count += 1

    ready_component_count += _ratio_component_findings(
        "preflight",
        screen.preflight_ready,
        blocker_codes,
        attention_codes,
    )
    ready_component_count += _ratio_component_findings(
        "operator_safety",
        screen.operator_safety_ready,
        blocker_codes,
        attention_codes,
    )

    return tuple(blocker_codes), tuple(attention_codes), ready_component_count


def _ratio_component_findings(
    reason_stem: str,
    value: Decimal,
    blocker_codes: list[str],
    attention_codes: list[str],
) -> int:
    if value == ZERO:
        blocker_codes.append(f"probability_event_{reason_stem}_block")
        return 0
    if value < ONE:
        attention_codes.append(f"probability_event_{reason_stem}_watch")
        return 0
    return 1


def _recommendation_band(blocker_count: Decimal, attention_count: Decimal) -> str:
    if blocker_count > ZERO:
        return "block"
    if attention_count > ZERO:
        return "watch"
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


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("primary_reason_codes must be a tuple")
    if not value:
        raise ValueError("primary_reason_codes must not be empty")
    normalized: list[str] = []
    for reason_code in value:
        if type(reason_code) is not str or not reason_code:
            raise ValueError("primary_reason_codes must contain non-empty strings")
        if reason_code.strip() != reason_code or reason_code.lower() != reason_code:
            raise ValueError("primary_reason_codes must contain canonical codes")
        for part in reason_code.split("_"):
            if not part or not part.isalnum() or part != part.lower():
                raise ValueError("primary_reason_codes must contain canonical codes")
        if reason_code in normalized:
            raise ValueError("primary_reason_codes must be unique")
        normalized.append(reason_code)
    return tuple(normalized)


def _require_hard_flags(label: str, value: Any) -> None:
    require_paper_only_flags(label, value)


def _validate_report(report: ProbabilityEventScreenRecommendationReport) -> None:
    if report.blocker_count + report.attention_count > COMPONENT_COUNT:
        raise ValueError("blocker_count and attention_count exceed component count")
    expected_ready_ratio = _ratio(
        COMPONENT_COUNT - report.blocker_count - report.attention_count,
        COMPONENT_COUNT,
    )
    if report.ready_component_ratio != expected_ready_ratio:
        raise ValueError("ready_component_ratio must match blocker and attention counts")
    if report.recommendation_band != _recommendation_band(
        report.blocker_count,
        report.attention_count,
    ):
        raise ValueError("recommendation_band must match blocker and attention counts")

    if report.primary_reason_codes == (READY_REASON_CODE,):
        if report.blocker_count != ZERO or report.attention_count != ZERO:
            raise ValueError("ready reason requires no blockers or attention items")
        if report.ready_component_ratio != ONE:
            raise ValueError("ready reason requires all components ready")
        return

    if READY_REASON_CODE in report.primary_reason_codes:
        raise ValueError("ready reason cannot be combined with blocker or watch reasons")
    blocker_reason_count = _count(
        sum(1 for reason_code in report.primary_reason_codes if reason_code.endswith("_block")),
    )
    attention_reason_count = _count(
        sum(1 for reason_code in report.primary_reason_codes if reason_code.endswith("_watch")),
    )
    if blocker_reason_count != report.blocker_count:
        raise ValueError("blocker_count must match blocker reason codes")
    if attention_reason_count != report.attention_count:
        raise ValueError("attention_count must match watch reason codes")


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)
