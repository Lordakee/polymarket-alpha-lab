"""Pure paper/report candidate event-specificity scorer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal
from hashlib import sha256
from typing import Any


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
PASS_THRESHOLD = Decimal("0.800000")
BLOCK_THRESHOLD = Decimal("0.450000")
COMPONENT_CLEAR_THRESHOLD = Decimal("0.700000")
AMBIGUITY_CLEAR_THRESHOLD = Decimal("0.250000")
EVENT_DEFINITION_WEIGHT = Decimal("0.225000")
RESOLUTION_CRITERIA_WEIGHT = Decimal("0.225000")
MEASURABLE_OUTCOME_WEIGHT = Decimal("0.175000")
TIMEFRAME_SPECIFICITY_WEIGHT = Decimal("0.100000")
RESEARCHABILITY_WEIGHT = Decimal("0.100000")
THRESHOLD_PRECISION_WEIGHT = Decimal("0.100000")
AMBIGUITY_WEIGHT = Decimal("0.075000")
SCORE_STATUSES = ("pass", "watch", "block")
_UNSAFE_TERM_PARTS = (
    ("candidate", "_", "id"),
    ("market", "_", "id"),
    ("market", "_", "slug"),
    ("ques", "tion"),
    ("source", "_", "ref"),
    ("source", "_", "url"),
    ("source", "_", "text"),
    ("d", "sn"),
    ("ta", "ble"),
    ("to", "ken"),
    ("wal", "let"),
    ("au", "th"),
    ("or", "der"),
    ("tra", "de"),
    ("posi", "tion"),
    ("b", "uy"),
    ("se", "ll"),
    ("recom", "mendation"),
    ("recom", "mend"),
)
_UNSAFE_TERMS = tuple("".join(parts) for parts in _UNSAFE_TERM_PARTS)
_DIGEST_FIELDS = (
    "event_definition_specificity_score",
    "resolution_criteria_clarity_score",
    "measurable_outcome_score",
    "timeframe_specificity_score",
    "researchability_score",
    "threshold_precision_score",
    "ambiguity_risk_score",
    "event_specificity_score",
    "score_status",
    "component_gaps",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class CandidateDecisionEventSpecificityScoreInput:
    event_definition_specificity_score: Decimal
    resolution_criteria_clarity_score: Decimal
    measurable_outcome_score: Decimal
    timeframe_specificity_score: Decimal
    researchability_score: Decimal
    threshold_precision_score: Decimal
    ambiguity_risk_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "event_definition_specificity_score",
            "resolution_criteria_clarity_score",
            "measurable_outcome_score",
            "timeframe_specificity_score",
            "researchability_score",
            "threshold_precision_score",
            "ambiguity_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        reject_candidate_decision_event_specificity_score_unsafe_payload(
            "candidate decision event specificity score input",
            self,
        )
        _require_paper_flags("candidate decision event specificity score input", self)


@dataclass(frozen=True)
class CandidateDecisionEventSpecificityScoreReport:
    event_definition_specificity_score: Decimal
    resolution_criteria_clarity_score: Decimal
    measurable_outcome_score: Decimal
    timeframe_specificity_score: Decimal
    researchability_score: Decimal
    threshold_precision_score: Decimal
    ambiguity_risk_score: Decimal
    event_specificity_score: Decimal
    score_status: str
    component_gaps: tuple[str, ...]
    reason_codes: tuple[str, ...]
    event_specificity_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "event_definition_specificity_score",
            "resolution_criteria_clarity_score",
            "measurable_outcome_score",
            "timeframe_specificity_score",
            "researchability_score",
            "threshold_precision_score",
            "ambiguity_risk_score",
            "event_specificity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_choice("score_status", self.score_status, SCORE_STATUSES)
        object.__setattr__(
            self,
            "component_gaps",
            _normalize_reason_codes("component_gaps", self.component_gaps),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report_consistency(self)
        reject_candidate_decision_event_specificity_score_unsafe_payload(
            "candidate decision event specificity score report",
            self,
        )
        _require_paper_flags("candidate decision event specificity score report", self)
        expected_digest = _event_specificity_digest(self)
        if self.event_specificity_digest:
            _require_canonical_digest("event_specificity_digest", self.event_specificity_digest)
            if self.event_specificity_digest != expected_digest:
                raise ValueError("event_specificity_digest must match report fields")
        else:
            object.__setattr__(self, "event_specificity_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return candidate_decision_event_specificity_score_payload(self)


def score_candidate_decision_event_specificity(
    score_input: CandidateDecisionEventSpecificityScoreInput,
) -> CandidateDecisionEventSpecificityScoreReport:
    if type(score_input) is not CandidateDecisionEventSpecificityScoreInput:
        raise ValueError("score_input must be a CandidateDecisionEventSpecificityScoreInput")
    reject_candidate_decision_event_specificity_score_unsafe_payload(
        "candidate decision event specificity score input",
        score_input,
    )
    _require_paper_flags("candidate decision event specificity score input", score_input)

    event_specificity_score = _event_specificity_score(
        score_input.event_definition_specificity_score,
        score_input.resolution_criteria_clarity_score,
        score_input.measurable_outcome_score,
        score_input.timeframe_specificity_score,
        score_input.researchability_score,
        score_input.threshold_precision_score,
        score_input.ambiguity_risk_score,
    )
    component_gaps = _component_gaps(
        score_input.event_definition_specificity_score,
        score_input.resolution_criteria_clarity_score,
        score_input.measurable_outcome_score,
        score_input.timeframe_specificity_score,
        score_input.researchability_score,
        score_input.threshold_precision_score,
        score_input.ambiguity_risk_score,
    )
    score_status = _score_status(event_specificity_score, component_gaps)

    return CandidateDecisionEventSpecificityScoreReport(
        event_definition_specificity_score=score_input.event_definition_specificity_score,
        resolution_criteria_clarity_score=score_input.resolution_criteria_clarity_score,
        measurable_outcome_score=score_input.measurable_outcome_score,
        timeframe_specificity_score=score_input.timeframe_specificity_score,
        researchability_score=score_input.researchability_score,
        threshold_precision_score=score_input.threshold_precision_score,
        ambiguity_risk_score=score_input.ambiguity_risk_score,
        event_specificity_score=event_specificity_score,
        score_status=score_status,
        component_gaps=component_gaps,
        reason_codes=_reason_codes(score_input.reason_codes, score_status),
    )


def candidate_decision_event_specificity_score_payload(
    result: CandidateDecisionEventSpecificityScoreReport,
) -> dict[str, Any]:
    if type(result) is not CandidateDecisionEventSpecificityScoreReport:
        raise ValueError("result must be a CandidateDecisionEventSpecificityScoreReport")
    _require_paper_flags("candidate decision event specificity score report", result)
    if result.event_specificity_digest != _event_specificity_digest(result):
        raise ValueError("event_specificity_digest must match report fields")
    reject_candidate_decision_event_specificity_score_unsafe_payload(
        "candidate decision event specificity score report",
        result,
    )
    return _json_ready(asdict(result))


def reject_candidate_decision_event_specificity_score_unsafe_payload(
    label: str,
    payload: object,
) -> None:
    for item in _iter_public_strings(payload):
        lowered = item.lower()
        if any(term in lowered for term in _UNSAFE_TERMS):
            raise ValueError(f"unsafe public payload entry in {label}")


def _event_specificity_score(
    event_definition_specificity_score: Decimal,
    resolution_criteria_clarity_score: Decimal,
    measurable_outcome_score: Decimal,
    timeframe_specificity_score: Decimal,
    researchability_score: Decimal,
    threshold_precision_score: Decimal,
    ambiguity_risk_score: Decimal,
) -> Decimal:
    return _normalize_ratio(
        "event_specificity_score",
        event_definition_specificity_score * EVENT_DEFINITION_WEIGHT
        + resolution_criteria_clarity_score * RESOLUTION_CRITERIA_WEIGHT
        + measurable_outcome_score * MEASURABLE_OUTCOME_WEIGHT
        + timeframe_specificity_score * TIMEFRAME_SPECIFICITY_WEIGHT
        + researchability_score * RESEARCHABILITY_WEIGHT
        + threshold_precision_score * THRESHOLD_PRECISION_WEIGHT
        + (ONE - ambiguity_risk_score) * AMBIGUITY_WEIGHT,
    )


def _component_gaps(
    event_definition_specificity_score: Decimal,
    resolution_criteria_clarity_score: Decimal,
    measurable_outcome_score: Decimal,
    timeframe_specificity_score: Decimal,
    researchability_score: Decimal,
    threshold_precision_score: Decimal,
    ambiguity_risk_score: Decimal,
) -> tuple[str, ...]:
    gaps = []
    if event_definition_specificity_score < COMPONENT_CLEAR_THRESHOLD:
        gaps.append("event_definition_specificity")
    if resolution_criteria_clarity_score < COMPONENT_CLEAR_THRESHOLD:
        gaps.append("resolution_criteria_clarity")
    if measurable_outcome_score < COMPONENT_CLEAR_THRESHOLD:
        gaps.append("measurable_outcome")
    if timeframe_specificity_score < COMPONENT_CLEAR_THRESHOLD:
        gaps.append("timeframe_specificity")
    if researchability_score < COMPONENT_CLEAR_THRESHOLD:
        gaps.append("researchability")
    if threshold_precision_score < COMPONENT_CLEAR_THRESHOLD:
        gaps.append("threshold_precision")
    if ambiguity_risk_score > AMBIGUITY_CLEAR_THRESHOLD:
        gaps.append("ambiguity_risk")
    return tuple(gaps)


def _score_status(
    event_specificity_score: Decimal,
    component_gaps: tuple[str, ...],
) -> str:
    if event_specificity_score < BLOCK_THRESHOLD:
        return "block"
    if event_specificity_score >= PASS_THRESHOLD and not component_gaps:
        return "pass"
    return "watch"


def _reason_codes(existing: tuple[str, ...], score_status: str) -> tuple[str, ...]:
    additions = (
        "event_specificity_score",
        f"status_{score_status}",
        "definition_specific",
        "criteria_decidable",
        "outcome_measurable",
        "timeframe_specific",
        "research_context_available",
        "threshold_precise",
        "ambiguity_low",
    )
    if score_status == "watch":
        additions = (
            "event_specificity_score",
            "status_watch",
            "definition_specific",
            "criteria_unclear",
            "outcome_measurable",
            "timeframe_incomplete",
            "research_context_available",
            "threshold_imprecise",
            "ambiguity_elevated",
        )
    if score_status == "block":
        additions = (
            "event_specificity_score",
            "status_block",
            "definition_too_broad",
            "criteria_unclear",
            "outcome_not_measurable",
            "timeframe_incomplete",
            "research_context_insufficient",
            "threshold_imprecise",
            "ambiguity_high",
        )
    return _append_reason_codes(existing, additions)


def _append_reason_codes(
    existing: tuple[str, ...],
    additions: tuple[str, ...],
) -> tuple[str, ...]:
    values = list(existing)
    for addition in additions:
        if addition not in values:
            values.append(addition)
    return tuple(values)


def _validate_report_consistency(
    result: CandidateDecisionEventSpecificityScoreReport,
) -> None:
    expected_score = _event_specificity_score(
        result.event_definition_specificity_score,
        result.resolution_criteria_clarity_score,
        result.measurable_outcome_score,
        result.timeframe_specificity_score,
        result.researchability_score,
        result.threshold_precision_score,
        result.ambiguity_risk_score,
    )
    if result.event_specificity_score != expected_score:
        raise ValueError("event_specificity_score must match component scores")
    expected_gaps = _component_gaps(
        result.event_definition_specificity_score,
        result.resolution_criteria_clarity_score,
        result.measurable_outcome_score,
        result.timeframe_specificity_score,
        result.researchability_score,
        result.threshold_precision_score,
        result.ambiguity_risk_score,
    )
    expected_status = _score_status(result.event_specificity_score, expected_gaps)
    if result.score_status != expected_status:
        raise ValueError("score_status must match event_specificity_score")
    if result.component_gaps != expected_gaps:
        raise ValueError("component_gaps must match component scores")
    if result.reason_codes != _reason_codes((), result.score_status):
        expected_with_prefix = _reason_codes(
            _reason_code_prefix(result.reason_codes, result.score_status),
            result.score_status,
        )
        if result.reason_codes != expected_with_prefix:
            raise ValueError("reason_codes must match score status")


def _reason_code_prefix(
    reason_codes: tuple[str, ...],
    score_status: str,
) -> tuple[str, ...]:
    additions = _reason_codes((), score_status)
    if len(reason_codes) < len(additions):
        return reason_codes
    prefix = reason_codes[: len(reason_codes) - len(additions)]
    return prefix


def _event_specificity_digest(
    result: CandidateDecisionEventSpecificityScoreReport,
) -> str:
    parts = tuple(
        f"{field_name}={_digest_value(getattr(result, field_name))}"
        for field_name in _DIGEST_FIELDS
    )
    return sha256("|".join(parts).encode("utf-8")).hexdigest()


def _digest_value(value: object) -> str:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, tuple):
        return "[" + ",".join(_digest_value(item) for item in value) + "]"
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) is str:
        return value
    raise ValueError("digest value must be public scalar data")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    return value


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between {ZERO} and {ONE}")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM)


def _require_choice(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values!r}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_canonical_digest(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be lowercase hex")


def _require_paper_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _iter_public_strings(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_public_strings(asdict(value))
    if isinstance(value, dict):
        items: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            items.append(key)
            items.extend(_iter_public_strings(item))
        return tuple(items)
    if type(value) is str:
        return (value,)
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            items.extend(_iter_public_strings(item))
        return tuple(items)
    return ()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, int) and not isinstance(value, bool):
        raise ValueError("JSON value must not be an int")
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


__all__ = (
    "SCORE_STATUSES",
    "CandidateDecisionEventSpecificityScoreInput",
    "CandidateDecisionEventSpecificityScoreReport",
    "score_candidate_decision_event_specificity",
    "candidate_decision_event_specificity_score_payload",
    "reject_candidate_decision_event_specificity_score_unsafe_payload",
)
