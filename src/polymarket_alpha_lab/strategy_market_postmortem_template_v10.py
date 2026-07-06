"""Paper-only readonly market postmortem template."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
BPS_MULTIPLIER = Decimal("10000.000000")
MATERIAL_CALIBRATION_DELTA_BPS = Decimal("500.000000")
BLOCKING_RESOLUTION_AMBIGUITY_SCORE = Decimal("0.700000")


@dataclass(frozen=True)
class MarketPostmortemTemplateInput:
    market_id: str
    category: str
    forecast_probability: Decimal
    settled_outcome_probability: Decimal
    entry_price_probability: Decimal
    cost_adjusted_edge_bps: Decimal
    source_gap_count: Decimal
    resolution_ambiguity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "market_id", _normalize_canonical_string("market_id", self.market_id))
        object.__setattr__(self, "category", _normalize_canonical_string("category", self.category))
        object.__setattr__(
            self,
            "forecast_probability",
            _normalize_probability("forecast_probability", self.forecast_probability),
        )
        object.__setattr__(
            self,
            "settled_outcome_probability",
            _normalize_binary_probability(
                "settled_outcome_probability",
                self.settled_outcome_probability,
            ),
        )
        object.__setattr__(
            self,
            "entry_price_probability",
            _normalize_probability("entry_price_probability", self.entry_price_probability),
        )
        object.__setattr__(
            self,
            "cost_adjusted_edge_bps",
            _normalize_decimal("cost_adjusted_edge_bps", self.cost_adjusted_edge_bps),
        )
        object.__setattr__(
            self,
            "source_gap_count",
            _normalize_nonnegative_whole_decimal("source_gap_count", self.source_gap_count),
        )
        object.__setattr__(
            self,
            "resolution_ambiguity_score",
            _normalize_probability(
                "resolution_ambiguity_score",
                self.resolution_ambiguity_score,
            ),
        )
        reject_unsafe_surface_fields("market postmortem template input", self)
        require_paper_only_flags("market postmortem template input", self)


@dataclass(frozen=True)
class MarketPostmortemTemplateResult:
    market_id: str
    category: str
    forecast_probability: Decimal
    settled_outcome_probability: Decimal
    entry_price_probability: Decimal
    cost_adjusted_edge_bps: Decimal
    source_gap_count: Decimal
    resolution_ambiguity_score: Decimal
    postmortem_status: str
    lesson_tags: tuple[str, ...]
    calibration_delta_bps: Decimal
    followup_actions: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "market_id", _normalize_canonical_string("market_id", self.market_id))
        object.__setattr__(self, "category", _normalize_canonical_string("category", self.category))
        object.__setattr__(
            self,
            "forecast_probability",
            _normalize_probability("forecast_probability", self.forecast_probability),
        )
        object.__setattr__(
            self,
            "settled_outcome_probability",
            _normalize_binary_probability(
                "settled_outcome_probability",
                self.settled_outcome_probability,
            ),
        )
        object.__setattr__(
            self,
            "entry_price_probability",
            _normalize_probability("entry_price_probability", self.entry_price_probability),
        )
        for field_name in (
            "cost_adjusted_edge_bps",
            "calibration_delta_bps",
        ):
            object.__setattr__(self, field_name, _normalize_decimal(field_name, getattr(self, field_name)))
        object.__setattr__(
            self,
            "source_gap_count",
            _normalize_nonnegative_whole_decimal("source_gap_count", self.source_gap_count),
        )
        object.__setattr__(
            self,
            "resolution_ambiguity_score",
            _normalize_probability(
                "resolution_ambiguity_score",
                self.resolution_ambiguity_score,
            ),
        )
        if self.postmortem_status not in ("pass", "watch", "blocked"):
            raise ValueError("postmortem_status must be pass, watch, or blocked")
        object.__setattr__(self, "lesson_tags", _normalize_string_tuple("lesson_tags", self.lesson_tags))
        object.__setattr__(
            self,
            "followup_actions",
            _normalize_string_tuple("followup_actions", self.followup_actions),
        )
        object.__setattr__(self, "reason_codes", _normalize_string_tuple("reason_codes", self.reason_codes))
        reject_unsafe_surface_fields("market postmortem template result", self)
        require_paper_only_flags("market postmortem template result", self)

    @property
    def payload(self) -> dict[str, Any]:
        return market_postmortem_template_payload(self)


def build_market_postmortem_template(
    template_input: MarketPostmortemTemplateInput,
) -> MarketPostmortemTemplateResult:
    if type(template_input) is not MarketPostmortemTemplateInput:
        raise ValueError("template_input must be a MarketPostmortemTemplateInput")
    require_paper_only_flags("market postmortem template input", template_input)
    reject_unsafe_surface_fields("market postmortem template input", template_input)

    calibration_delta_bps = _normalize_decimal(
        "calibration_delta_bps",
        (
            template_input.settled_outcome_probability
            - template_input.forecast_probability
        )
        * BPS_MULTIPLIER,
    )
    status = _postmortem_status(
        calibration_delta_bps=calibration_delta_bps,
        source_gap_count=template_input.source_gap_count,
        resolution_ambiguity_score=template_input.resolution_ambiguity_score,
        cost_adjusted_edge_bps=template_input.cost_adjusted_edge_bps,
    )

    return MarketPostmortemTemplateResult(
        market_id=template_input.market_id,
        category=template_input.category,
        forecast_probability=template_input.forecast_probability,
        settled_outcome_probability=template_input.settled_outcome_probability,
        entry_price_probability=template_input.entry_price_probability,
        cost_adjusted_edge_bps=template_input.cost_adjusted_edge_bps,
        source_gap_count=template_input.source_gap_count,
        resolution_ambiguity_score=template_input.resolution_ambiguity_score,
        postmortem_status=status,
        lesson_tags=_lesson_tags(
            calibration_delta_bps=calibration_delta_bps,
            forecast_probability=template_input.forecast_probability,
            entry_price_probability=template_input.entry_price_probability,
            cost_adjusted_edge_bps=template_input.cost_adjusted_edge_bps,
            source_gap_count=template_input.source_gap_count,
            resolution_ambiguity_score=template_input.resolution_ambiguity_score,
        ),
        calibration_delta_bps=calibration_delta_bps,
        followup_actions=_followup_actions(
            calibration_delta_bps=calibration_delta_bps,
            source_gap_count=template_input.source_gap_count,
            resolution_ambiguity_score=template_input.resolution_ambiguity_score,
            cost_adjusted_edge_bps=template_input.cost_adjusted_edge_bps,
        ),
        reason_codes=_reason_codes(
            postmortem_status=status,
            calibration_delta_bps=calibration_delta_bps,
            source_gap_count=template_input.source_gap_count,
            resolution_ambiguity_score=template_input.resolution_ambiguity_score,
            cost_adjusted_edge_bps=template_input.cost_adjusted_edge_bps,
        ),
    )


def market_postmortem_template_payload(
    report: MarketPostmortemTemplateResult,
) -> dict[str, Any]:
    if type(report) is not MarketPostmortemTemplateResult:
        raise ValueError("report must be a MarketPostmortemTemplateResult")
    require_paper_only_flags("market postmortem template result", report)
    reject_unsafe_surface_fields("market postmortem template result", report)
    return json_ready_no_floats(
        {
            "market_id": report.market_id,
            "category": report.category,
            "forecast_probability": report.forecast_probability,
            "settled_outcome_probability": report.settled_outcome_probability,
            "entry_price_probability": report.entry_price_probability,
            "cost_adjusted_edge_bps": report.cost_adjusted_edge_bps,
            "source_gap_count": report.source_gap_count,
            "resolution_ambiguity_score": report.resolution_ambiguity_score,
            "postmortem_status": report.postmortem_status,
            "lesson_tags": report.lesson_tags,
            "calibration_delta_bps": report.calibration_delta_bps,
            "followup_actions": report.followup_actions,
            "reason_codes": report.reason_codes,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )


def _postmortem_status(
    *,
    calibration_delta_bps: Decimal,
    source_gap_count: Decimal,
    resolution_ambiguity_score: Decimal,
    cost_adjusted_edge_bps: Decimal,
) -> str:
    if (
        resolution_ambiguity_score >= BLOCKING_RESOLUTION_AMBIGUITY_SCORE
        or cost_adjusted_edge_bps <= ZERO
    ):
        return "blocked"
    if (
        abs(calibration_delta_bps) <= MATERIAL_CALIBRATION_DELTA_BPS
        and source_gap_count == ZERO
        and resolution_ambiguity_score == ZERO
    ):
        return "pass"
    return "watch"


def _lesson_tags(
    *,
    calibration_delta_bps: Decimal,
    forecast_probability: Decimal,
    entry_price_probability: Decimal,
    cost_adjusted_edge_bps: Decimal,
    source_gap_count: Decimal,
    resolution_ambiguity_score: Decimal,
) -> tuple[str, ...]:
    tags: list[str] = []
    if abs(calibration_delta_bps) <= MATERIAL_CALIBRATION_DELTA_BPS:
        tags.append("well_calibrated")
    elif calibration_delta_bps > ZERO:
        tags.append("underestimated_settled_outcome")
    else:
        tags.append("overestimated_settled_outcome")

    if entry_price_probability < forecast_probability:
        tags.append("entry_below_forecast")
    elif entry_price_probability > forecast_probability:
        tags.append("entry_above_forecast")
    else:
        tags.append("entry_at_forecast")

    if source_gap_count > ZERO:
        tags.append("source_gap_present")
    if cost_adjusted_edge_bps <= ZERO:
        tags.append("cost_adjusted_edge_nonpositive")
    if resolution_ambiguity_score > ZERO:
        tags.append("resolution_ambiguity_present")
    return tuple(tags)


def _followup_actions(
    *,
    calibration_delta_bps: Decimal,
    source_gap_count: Decimal,
    resolution_ambiguity_score: Decimal,
    cost_adjusted_edge_bps: Decimal,
) -> tuple[str, ...]:
    actions: list[str] = []
    if abs(calibration_delta_bps) > MATERIAL_CALIBRATION_DELTA_BPS:
        actions.append("recalibrate_category_forecast_priors")
    if source_gap_count > ZERO:
        actions.append("close_source_coverage_gap")
    if cost_adjusted_edge_bps <= ZERO:
        actions.append("tighten_cost_adjusted_entry_gate")
    if resolution_ambiguity_score > ZERO:
        actions.append("review_resolution_rules_before_next_entry")
    if not actions:
        actions.append("record_market_as_calibration_reference")
    return tuple(actions)


def _reason_codes(
    *,
    postmortem_status: str,
    calibration_delta_bps: Decimal,
    source_gap_count: Decimal,
    resolution_ambiguity_score: Decimal,
    cost_adjusted_edge_bps: Decimal,
) -> tuple[str, ...]:
    codes = ["market_postmortem_template"]
    if abs(calibration_delta_bps) > MATERIAL_CALIBRATION_DELTA_BPS:
        codes.append("calibration_delta_material")
    else:
        codes.append("calibration_delta_within_threshold")

    if source_gap_count > ZERO:
        codes.append("source_gap_detected")
    else:
        codes.append("no_source_gap")

    if resolution_ambiguity_score >= BLOCKING_RESOLUTION_AMBIGUITY_SCORE:
        codes.append("resolution_ambiguity_blocked")
    elif resolution_ambiguity_score > ZERO:
        codes.append("resolution_ambiguity_detected")
    else:
        codes.append("resolution_clear")

    if cost_adjusted_edge_bps > ZERO:
        codes.append("cost_adjusted_edge_positive")
    else:
        codes.append("cost_adjusted_edge_nonpositive")

    codes.append(f"postmortem_{postmortem_status}")
    return tuple(codes)


def _normalize_probability(field_name: str, value: Any) -> Decimal:
    decimal = _normalize_decimal(field_name, value)
    if decimal < ZERO or decimal > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal


def _normalize_binary_probability(field_name: str, value: Any) -> Decimal:
    decimal = _normalize_probability(field_name, value)
    if decimal not in (ZERO, ONE):
        raise ValueError(f"{field_name} must be 0 or 1")
    return decimal


def _normalize_nonnegative_whole_decimal(field_name: str, value: Any) -> Decimal:
    decimal = _normalize_decimal(field_name, value)
    if decimal < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal != decimal.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal


def _normalize_decimal(field_name: str, value: Any) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM)


def _normalize_string_tuple(field_name: str, value: Any) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for item in value:
        _normalize_canonical_string(field_name, item)
    return value


def _normalize_canonical_string(field_name: str, value: Any) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    return value


__all__ = (
    "MarketPostmortemTemplateInput",
    "MarketPostmortemTemplateResult",
    "build_market_postmortem_template",
    "market_postmortem_template_payload",
)
