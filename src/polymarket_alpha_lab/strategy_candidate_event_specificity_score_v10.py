"""Pure report-only event specificity scoring for candidate contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Any


SPECIFICITY_STATUSES = ("pass", "watch", "blocked")

REQUIRED_FOLLOWUPS = (
    "rewrite_ambiguous_market_terms",
    "add_measurable_resolution_criteria",
    "verify_resolution_source_alignment",
    "clarify_resolution_deadline",
    "reduce_adjudication_complexity",
)

REASON_CODES = (
    "specificity_clear",
    "ambiguous_terms_present",
    "ambiguous_terms_high",
    "measurable_resolution_criteria_gap",
    "source_alignment_gap",
    "source_alignment_conflict",
    "deadline_clarity_gap",
    "adjudication_complexity_present",
    "adjudication_complexity_high",
)

SCORE_QUANT = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")


@dataclass(frozen=True)
class StrategyCandidateEventSpecificityScoreV10Input:
    candidate_id: str
    ambiguous_term_count: Decimal
    measurable_resolution_criteria_score: Decimal
    source_alignment_score: Decimal
    deadline_clarity_score: Decimal
    adjudication_complexity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateEventSpecificityScoreV10Input:
            raise ValueError("input must be a StrategyCandidateEventSpecificityScoreV10Input")
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_whole_decimal_count("ambiguous_term_count", self.ambiguous_term_count)
        _require_ratio_decimal(
            "measurable_resolution_criteria_score",
            self.measurable_resolution_criteria_score,
        )
        _require_ratio_decimal("source_alignment_score", self.source_alignment_score)
        _require_ratio_decimal("deadline_clarity_score", self.deadline_clarity_score)
        _require_ratio_decimal(
            "adjudication_complexity_score",
            self.adjudication_complexity_score,
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyCandidateEventSpecificityScoreV10Report:
    candidate_id: str
    ambiguous_term_count: Decimal
    measurable_resolution_criteria_score: Decimal
    source_alignment_score: Decimal
    deadline_clarity_score: Decimal
    adjudication_complexity_score: Decimal
    specificity_status: str
    specificity_risk_score: Decimal
    required_followups: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateEventSpecificityScoreV10Report:
            raise ValueError("report must be a StrategyCandidateEventSpecificityScoreV10Report")
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_whole_decimal_count("ambiguous_term_count", self.ambiguous_term_count)
        _require_ratio_decimal(
            "measurable_resolution_criteria_score",
            self.measurable_resolution_criteria_score,
        )
        _require_ratio_decimal("source_alignment_score", self.source_alignment_score)
        _require_ratio_decimal("deadline_clarity_score", self.deadline_clarity_score)
        _require_ratio_decimal(
            "adjudication_complexity_score",
            self.adjudication_complexity_score,
        )
        _require_member("specificity_status", self.specificity_status, SPECIFICITY_STATUSES)
        _require_ratio_decimal("specificity_risk_score", self.specificity_risk_score)
        object.__setattr__(
            self,
            "required_followups",
            _normalize_string_tuple(
                "required_followups",
                self.required_followups,
                REQUIRED_FOLLOWUPS,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple(
                "reason_codes",
                self.reason_codes,
                REASON_CODES,
                allow_empty=False,
            ),
        )

        expected_score = _specificity_risk_score(
            ambiguous_term_count=self.ambiguous_term_count,
            measurable_resolution_criteria_score=(
                self.measurable_resolution_criteria_score
            ),
            source_alignment_score=self.source_alignment_score,
            deadline_clarity_score=self.deadline_clarity_score,
            adjudication_complexity_score=self.adjudication_complexity_score,
        )
        if self.specificity_risk_score != expected_score:
            raise ValueError("specificity_risk_score must match specificity inputs")

        expected_status = _specificity_status(
            specificity_risk_score=self.specificity_risk_score,
            measurable_resolution_criteria_score=(
                self.measurable_resolution_criteria_score
            ),
            source_alignment_score=self.source_alignment_score,
            deadline_clarity_score=self.deadline_clarity_score,
            adjudication_complexity_score=self.adjudication_complexity_score,
        )
        if self.specificity_status != expected_status:
            raise ValueError("specificity_status must match specificity inputs")

        expected_followups = _required_followups(
            ambiguous_term_count=self.ambiguous_term_count,
            measurable_resolution_criteria_score=(
                self.measurable_resolution_criteria_score
            ),
            source_alignment_score=self.source_alignment_score,
            deadline_clarity_score=self.deadline_clarity_score,
            adjudication_complexity_score=self.adjudication_complexity_score,
        )
        if self.required_followups != expected_followups:
            raise ValueError("required_followups must match specificity inputs")

        expected_reason_codes = _reason_codes(
            ambiguous_term_count=self.ambiguous_term_count,
            measurable_resolution_criteria_score=(
                self.measurable_resolution_criteria_score
            ),
            source_alignment_score=self.source_alignment_score,
            deadline_clarity_score=self.deadline_clarity_score,
            adjudication_complexity_score=self.adjudication_complexity_score,
        )
        if self.reason_codes != expected_reason_codes:
            raise ValueError("reason_codes must match specificity inputs")
        _require_hard_flags(self)

    @property
    def payload(self) -> dict[str, Any]:
        return _payload_value(asdict(self))


def build_strategy_candidate_event_specificity_score_v10_report(
    *,
    candidate_id: str,
    ambiguous_term_count: Decimal,
    measurable_resolution_criteria_score: Decimal,
    source_alignment_score: Decimal,
    deadline_clarity_score: Decimal,
    adjudication_complexity_score: Decimal,
) -> StrategyCandidateEventSpecificityScoreV10Report:
    input_row = StrategyCandidateEventSpecificityScoreV10Input(
        candidate_id=candidate_id,
        ambiguous_term_count=ambiguous_term_count,
        measurable_resolution_criteria_score=measurable_resolution_criteria_score,
        source_alignment_score=source_alignment_score,
        deadline_clarity_score=deadline_clarity_score,
        adjudication_complexity_score=adjudication_complexity_score,
    )
    score = _specificity_risk_score(
        ambiguous_term_count=input_row.ambiguous_term_count,
        measurable_resolution_criteria_score=(
            input_row.measurable_resolution_criteria_score
        ),
        source_alignment_score=input_row.source_alignment_score,
        deadline_clarity_score=input_row.deadline_clarity_score,
        adjudication_complexity_score=input_row.adjudication_complexity_score,
    )
    return StrategyCandidateEventSpecificityScoreV10Report(
        candidate_id=input_row.candidate_id,
        ambiguous_term_count=input_row.ambiguous_term_count,
        measurable_resolution_criteria_score=(
            input_row.measurable_resolution_criteria_score
        ),
        source_alignment_score=input_row.source_alignment_score,
        deadline_clarity_score=input_row.deadline_clarity_score,
        adjudication_complexity_score=input_row.adjudication_complexity_score,
        specificity_status=_specificity_status(
            specificity_risk_score=score,
            measurable_resolution_criteria_score=(
                input_row.measurable_resolution_criteria_score
            ),
            source_alignment_score=input_row.source_alignment_score,
            deadline_clarity_score=input_row.deadline_clarity_score,
            adjudication_complexity_score=input_row.adjudication_complexity_score,
        ),
        specificity_risk_score=score,
        required_followups=_required_followups(
            ambiguous_term_count=input_row.ambiguous_term_count,
            measurable_resolution_criteria_score=(
                input_row.measurable_resolution_criteria_score
            ),
            source_alignment_score=input_row.source_alignment_score,
            deadline_clarity_score=input_row.deadline_clarity_score,
            adjudication_complexity_score=input_row.adjudication_complexity_score,
        ),
        reason_codes=_reason_codes(
            ambiguous_term_count=input_row.ambiguous_term_count,
            measurable_resolution_criteria_score=(
                input_row.measurable_resolution_criteria_score
            ),
            source_alignment_score=input_row.source_alignment_score,
            deadline_clarity_score=input_row.deadline_clarity_score,
            adjudication_complexity_score=input_row.adjudication_complexity_score,
        ),
    )


def strategy_candidate_event_specificity_score_v10_payload(
    report: StrategyCandidateEventSpecificityScoreV10Report,
) -> dict[str, Any]:
    if type(report) is not StrategyCandidateEventSpecificityScoreV10Report:
        raise ValueError("report must be a StrategyCandidateEventSpecificityScoreV10Report")
    _require_hard_flags(report)
    return report.payload


def _specificity_risk_score(
    *,
    ambiguous_term_count: Decimal,
    measurable_resolution_criteria_score: Decimal,
    source_alignment_score: Decimal,
    deadline_clarity_score: Decimal,
    adjudication_complexity_score: Decimal,
) -> Decimal:
    score = (
        min(ambiguous_term_count, Decimal("5")) * Decimal("0.050000")
        + (ONE - measurable_resolution_criteria_score) * Decimal("0.250000")
        + (ONE - source_alignment_score) * Decimal("0.200000")
        + (ONE - deadline_clarity_score) * Decimal("0.200000")
        + adjudication_complexity_score * Decimal("0.125000")
        + _severe_specificity_bonus(
            ambiguous_term_count=ambiguous_term_count,
            source_alignment_score=source_alignment_score,
            adjudication_complexity_score=adjudication_complexity_score,
        )
    )
    return min(max(score, ZERO), ONE).quantize(SCORE_QUANT)


def _severe_specificity_bonus(
    *,
    ambiguous_term_count: Decimal,
    source_alignment_score: Decimal,
    adjudication_complexity_score: Decimal,
) -> Decimal:
    bonus = ZERO
    if ambiguous_term_count >= Decimal("5"):
        bonus += Decimal("0.050000")
    if source_alignment_score <= Decimal("0.250000"):
        bonus += Decimal("0.050000")
    if adjudication_complexity_score >= Decimal("0.850000"):
        bonus += Decimal("0.050000")
    return bonus


def _specificity_status(
    *,
    specificity_risk_score: Decimal,
    measurable_resolution_criteria_score: Decimal,
    source_alignment_score: Decimal,
    deadline_clarity_score: Decimal,
    adjudication_complexity_score: Decimal,
) -> str:
    if specificity_risk_score >= Decimal("0.700000"):
        return "blocked"
    if source_alignment_score <= Decimal("0.250000"):
        return "blocked"
    if measurable_resolution_criteria_score <= Decimal("0.250000"):
        return "blocked"
    if deadline_clarity_score <= Decimal("0.250000"):
        return "blocked"
    if adjudication_complexity_score >= Decimal("0.850000"):
        return "blocked"
    if specificity_risk_score > ZERO:
        return "watch"
    return "pass"


def _required_followups(
    *,
    ambiguous_term_count: Decimal,
    measurable_resolution_criteria_score: Decimal,
    source_alignment_score: Decimal,
    deadline_clarity_score: Decimal,
    adjudication_complexity_score: Decimal,
) -> tuple[str, ...]:
    values: list[str] = []
    if ambiguous_term_count > ZERO:
        values.append("rewrite_ambiguous_market_terms")
    if measurable_resolution_criteria_score < Decimal("0.750000"):
        values.append("add_measurable_resolution_criteria")
    if source_alignment_score < Decimal("0.750000"):
        values.append("verify_resolution_source_alignment")
    if deadline_clarity_score < Decimal("0.750000"):
        values.append("clarify_resolution_deadline")
    if adjudication_complexity_score >= Decimal("0.750000"):
        values.append("reduce_adjudication_complexity")
    return tuple(values)


def _reason_codes(
    *,
    ambiguous_term_count: Decimal,
    measurable_resolution_criteria_score: Decimal,
    source_alignment_score: Decimal,
    deadline_clarity_score: Decimal,
    adjudication_complexity_score: Decimal,
) -> tuple[str, ...]:
    values: list[str] = []
    if ambiguous_term_count >= Decimal("5"):
        values.append("ambiguous_terms_high")
    elif ambiguous_term_count > ZERO:
        values.append("ambiguous_terms_present")
    if measurable_resolution_criteria_score < Decimal("0.750000"):
        values.append("measurable_resolution_criteria_gap")
    if source_alignment_score <= Decimal("0.250000"):
        values.append("source_alignment_conflict")
    elif source_alignment_score < Decimal("0.750000"):
        values.append("source_alignment_gap")
    if deadline_clarity_score < Decimal("0.750000"):
        values.append("deadline_clarity_gap")
    if adjudication_complexity_score >= Decimal("0.750000"):
        values.append("adjudication_complexity_high")
    elif adjudication_complexity_score > ZERO:
        values.append("adjudication_complexity_present")
    if not values:
        values.append("specificity_clear")
    return tuple(values)


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_whole_decimal_count(field_name: str, value: Decimal) -> None:
    _require_nonnegative_decimal(field_name, value)
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")


def _require_ratio_decimal(field_name: str, value: Decimal) -> None:
    _require_nonnegative_decimal(field_name, value)
    if value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")


def _require_member(field_name: str, value: str, values: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in values:
        raise ValueError(f"{field_name} must be known")


def _normalize_string_tuple(
    field_name: str,
    values: tuple[str, ...],
    allowed_values: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not allow_empty and not values:
        raise ValueError(f"{field_name} must contain at least one value")
    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} must not contain duplicates")
    for value in values:
        _require_member(field_name, value, allowed_values)
    return values


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _payload_value(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


__all__ = (
    "REASON_CODES",
    "REQUIRED_FOLLOWUPS",
    "SPECIFICITY_STATUSES",
    "StrategyCandidateEventSpecificityScoreV10Input",
    "StrategyCandidateEventSpecificityScoreV10Report",
    "build_strategy_candidate_event_specificity_score_v10_report",
    "strategy_candidate_event_specificity_score_v10_payload",
)
