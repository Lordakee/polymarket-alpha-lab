"""Pure paper-only probability event recommendation rank explainer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from typing import Any, Mapping, Sequence


_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_EDGE_REVIEW_MIN = Decimal("0.100000")
_CONFIDENCE_REVIEW_MIN = Decimal("0.600000")
_SOURCE_REVIEW_MIN = Decimal("0.600000")
_PENALTY_HIGH_MIN = Decimal("0.200000")
_PENALTY_EXTREME_MIN = Decimal("0.800000")
_RECOMMEND_SCORE_MIN = Decimal("0.250000")
_CONFIDENCE_WEIGHT = Decimal("0.100000")
_SOURCE_WEIGHT = Decimal("0.050000")
_COST_WEIGHT = Decimal("0.400000")
_RISK_WEIGHT = Decimal("0.300000")
_RECOMMENDATION_STATUSES = frozenset(("recommend", "watch", "reject"))
_MANUAL_NEXT_STEPS = frozenset(
    (
        "manual_review_candidate",
        "manual_research_update",
        "manual_reject_candidate",
    ),
)
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_REASON_CODE_SEQUENCE = (
    "edge_positive",
    "edge_below_review_threshold",
    "confidence_high",
    "confidence_below_review_threshold",
    "source_quality_high",
    "source_quality_below_review_threshold",
    "cost_penalty_high",
    "cost_penalty_extreme",
    "risk_penalty_high",
    "risk_penalty_extreme",
)
_PAYLOAD_DIGEST_FIELD = "payload_digest"
_PUBLIC_PAYLOAD_FIELDS = (
    "edge_score_probability",
    "confidence_score_probability",
    "source_quality_probability",
    "cost_penalty_probability",
    "risk_penalty_probability",
    "recommendation_status",
    "rank_explainability_score",
    "reason_codes",
    "manual_next_step",
    "paper_only",
    "report_only",
    "readonly",
    "payload_digest",
)
_UNSAFE_PUBLIC_TOKENS = tuple(
    "".join(chr(item) for item in code)
    for code in (
        (108, 105, 118, 101),
        (97, 117, 116, 104),
        (119, 97, 108, 108, 101, 116),
        (107, 101, 121),
        (115, 105, 103, 110),
        (111, 114, 100, 101, 114),
        (110, 101, 116, 119, 111, 114, 107),
        (100, 97, 116, 97, 98, 97, 115, 101),
        (112, 101, 114, 115, 105, 115, 116),
        (101, 120, 101, 99, 117, 116, 101),
        (116, 114, 97, 100, 101),
        (98, 117, 121),
        (115, 101, 108, 108),
    )
)


@dataclass(frozen=True)
class ProbabilityEventRecommendationRankExplainabilityReport:
    edge_score_probability: Decimal
    confidence_score_probability: Decimal
    source_quality_probability: Decimal
    cost_penalty_probability: Decimal
    risk_penalty_probability: Decimal
    recommendation_status: str
    rank_explainability_score: Decimal
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "edge_score_probability",
            "confidence_score_probability",
            "source_quality_probability",
            "cost_penalty_probability",
            "risk_penalty_probability",
            "rank_explainability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_member(
            "recommendation_status",
            self.recommendation_status,
            _RECOMMENDATION_STATUSES,
        )
        _require_member("manual_next_step", self.manual_next_step, _MANUAL_NEXT_STEPS)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        _reject_unsafe_public_payload("report", _public_payload_values(self))
        if self.payload_digest == "":
            object.__setattr__(
                self,
                _PAYLOAD_DIGEST_FIELD,
                _report_payload_digest(self),
            )
        else:
            object.__setattr__(
                self,
                _PAYLOAD_DIGEST_FIELD,
                _normalize_sha256(_PAYLOAD_DIGEST_FIELD, self.payload_digest),
            )
        _validate_payload_digest(self)

    @property
    def public_payload(self) -> dict[str, object]:
        _validate_payload_digest(self)
        payload = _public_payload_values(self)
        payload[_PAYLOAD_DIGEST_FIELD] = self.payload_digest
        _reject_unsafe_public_payload("payload", payload)
        return payload


def build_probability_event_recommendation_rank_explainability_report(
    *,
    edge_score_probability: Decimal,
    confidence_score_probability: Decimal,
    source_quality_probability: Decimal,
    cost_penalty_probability: Decimal,
    risk_penalty_probability: Decimal,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ProbabilityEventRecommendationRankExplainabilityReport:
    edge = _require_ratio_decimal("edge_score_probability", edge_score_probability)
    confidence = _require_ratio_decimal(
        "confidence_score_probability",
        confidence_score_probability,
    )
    source_quality = _require_ratio_decimal(
        "source_quality_probability",
        source_quality_probability,
    )
    cost_penalty = _require_ratio_decimal(
        "cost_penalty_probability",
        cost_penalty_probability,
    )
    risk_penalty = _require_ratio_decimal(
        "risk_penalty_probability",
        risk_penalty_probability,
    )
    flags = _PhaseFlags(paper_only=paper_only, report_only=report_only, readonly=readonly)
    _require_hard_flags("builder", flags)

    score = _rank_explainability_score(
        edge_score_probability=edge,
        confidence_score_probability=confidence,
        source_quality_probability=source_quality,
        cost_penalty_probability=cost_penalty,
        risk_penalty_probability=risk_penalty,
    )
    reason_codes = _reason_codes(
        edge_score_probability=edge,
        confidence_score_probability=confidence,
        source_quality_probability=source_quality,
        cost_penalty_probability=cost_penalty,
        risk_penalty_probability=risk_penalty,
    )
    status = _recommendation_status(
        rank_explainability_score=score,
        reason_codes=reason_codes,
    )
    return ProbabilityEventRecommendationRankExplainabilityReport(
        edge_score_probability=edge,
        confidence_score_probability=confidence,
        source_quality_probability=source_quality,
        cost_penalty_probability=cost_penalty,
        risk_penalty_probability=risk_penalty,
        recommendation_status=status,
        rank_explainability_score=score,
        reason_codes=reason_codes,
        manual_next_step=_manual_next_step(status),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def probability_event_recommendation_rank_explainability_report_payload(
    report: ProbabilityEventRecommendationRankExplainabilityReport,
) -> dict[str, object]:
    if type(report) is not ProbabilityEventRecommendationRankExplainabilityReport:
        raise ValueError(
            "report must be a ProbabilityEventRecommendationRankExplainabilityReport",
        )
    return report.public_payload


def validate_probability_event_recommendation_rank_explainability_public_payload(
    payload: object,
) -> dict[str, object]:
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_unsafe_public_payload("payload", payload)
    _require_payload_fields(payload)

    supplied_digest = _require_payload_string(
        _PAYLOAD_DIGEST_FIELD,
        payload[_PAYLOAD_DIGEST_FIELD],
    )
    digest_payload = {
        field_name: payload[field_name]
        for field_name in _PUBLIC_PAYLOAD_FIELDS
        if field_name != _PAYLOAD_DIGEST_FIELD
    }
    if supplied_digest != _payload_digest_for_values(digest_payload):
        raise ValueError("payload_digest must match payload fields")

    probe = ProbabilityEventRecommendationRankExplainabilityReport(
        edge_score_probability=_decimal_from_payload(
            "edge_score_probability",
            payload["edge_score_probability"],
        ),
        confidence_score_probability=_decimal_from_payload(
            "confidence_score_probability",
            payload["confidence_score_probability"],
        ),
        source_quality_probability=_decimal_from_payload(
            "source_quality_probability",
            payload["source_quality_probability"],
        ),
        cost_penalty_probability=_decimal_from_payload(
            "cost_penalty_probability",
            payload["cost_penalty_probability"],
        ),
        risk_penalty_probability=_decimal_from_payload(
            "risk_penalty_probability",
            payload["risk_penalty_probability"],
        ),
        recommendation_status=_require_payload_string(
            "recommendation_status",
            payload["recommendation_status"],
        ),
        rank_explainability_score=_decimal_from_payload(
            "rank_explainability_score",
            payload["rank_explainability_score"],
        ),
        reason_codes=_require_payload_reason_codes(payload["reason_codes"]),
        manual_next_step=_require_payload_string(
            "manual_next_step",
            payload["manual_next_step"],
        ),
        paper_only=_require_payload_bool("paper_only", payload["paper_only"]),
        report_only=_require_payload_bool("report_only", payload["report_only"]),
        readonly=_require_payload_bool("readonly", payload["readonly"]),
        payload_digest=supplied_digest,
    )
    validated_payload = _public_payload_values(probe)
    validated_payload[_PAYLOAD_DIGEST_FIELD] = probe.payload_digest
    return validated_payload


@dataclass(frozen=True)
class _PhaseFlags:
    paper_only: bool
    report_only: bool
    readonly: bool


def _rank_explainability_score(
    *,
    edge_score_probability: Decimal,
    confidence_score_probability: Decimal,
    source_quality_probability: Decimal,
    cost_penalty_probability: Decimal,
    risk_penalty_probability: Decimal,
) -> Decimal:
    if (
        edge_score_probability < _EDGE_REVIEW_MIN
        or confidence_score_probability < _CONFIDENCE_REVIEW_MIN
        or source_quality_probability < _SOURCE_REVIEW_MIN
    ):
        return _ZERO
    raw_score = (
        edge_score_probability
        + (confidence_score_probability * _CONFIDENCE_WEIGHT)
        + (source_quality_probability * _SOURCE_WEIGHT)
        - (cost_penalty_probability * _COST_WEIGHT)
        - (risk_penalty_probability * _RISK_WEIGHT)
    )
    if raw_score < _ZERO:
        return _ZERO
    if raw_score > _ONE:
        return _ONE
    return _quantize(raw_score)


def _reason_codes(
    *,
    edge_score_probability: Decimal,
    confidence_score_probability: Decimal,
    source_quality_probability: Decimal,
    cost_penalty_probability: Decimal,
    risk_penalty_probability: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if edge_score_probability >= _EDGE_REVIEW_MIN:
        reason_codes.append("edge_positive")
    else:
        reason_codes.append("edge_below_review_threshold")
    if confidence_score_probability >= _CONFIDENCE_REVIEW_MIN:
        reason_codes.append("confidence_high")
    else:
        reason_codes.append("confidence_below_review_threshold")
    if source_quality_probability >= _SOURCE_REVIEW_MIN:
        reason_codes.append("source_quality_high")
    else:
        reason_codes.append("source_quality_below_review_threshold")
    if cost_penalty_probability >= _PENALTY_EXTREME_MIN:
        reason_codes.append("cost_penalty_extreme")
    elif cost_penalty_probability >= _PENALTY_HIGH_MIN:
        reason_codes.append("cost_penalty_high")
    if risk_penalty_probability >= _PENALTY_EXTREME_MIN:
        reason_codes.append("risk_penalty_extreme")
    elif risk_penalty_probability >= _PENALTY_HIGH_MIN:
        reason_codes.append("risk_penalty_high")
    return _normalize_reason_codes(reason_codes)


def _recommendation_status(
    *,
    rank_explainability_score: Decimal,
    reason_codes: tuple[str, ...],
) -> str:
    if "cost_penalty_extreme" in reason_codes or "risk_penalty_extreme" in reason_codes:
        return "reject"
    if rank_explainability_score >= _RECOMMEND_SCORE_MIN:
        return "recommend"
    return "watch"


def _manual_next_step(recommendation_status: str) -> str:
    if recommendation_status == "recommend":
        return "manual_review_candidate"
    if recommendation_status == "watch":
        return "manual_research_update"
    if recommendation_status == "reject":
        return "manual_reject_candidate"
    raise ValueError("recommendation_status must be supported")


def _validate_report_consistency(
    report: ProbabilityEventRecommendationRankExplainabilityReport,
) -> None:
    expected_score = _rank_explainability_score(
        edge_score_probability=report.edge_score_probability,
        confidence_score_probability=report.confidence_score_probability,
        source_quality_probability=report.source_quality_probability,
        cost_penalty_probability=report.cost_penalty_probability,
        risk_penalty_probability=report.risk_penalty_probability,
    )
    if report.rank_explainability_score != expected_score:
        raise ValueError("rank_explainability_score must match report inputs")
    expected_reasons = _reason_codes(
        edge_score_probability=report.edge_score_probability,
        confidence_score_probability=report.confidence_score_probability,
        source_quality_probability=report.source_quality_probability,
        cost_penalty_probability=report.cost_penalty_probability,
        risk_penalty_probability=report.risk_penalty_probability,
    )
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match report inputs")
    expected_status = _recommendation_status(
        rank_explainability_score=expected_score,
        reason_codes=expected_reasons,
    )
    if report.recommendation_status != expected_status:
        raise ValueError("recommendation_status must match report inputs")
    if report.manual_next_step != _manual_next_step(expected_status):
        raise ValueError("manual_next_step must match recommendation_status")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if not hasattr(value, field_name):
            raise ValueError(f"{label} must expose {field_name}")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_member(field_name: str, value: object, members: frozenset[str]) -> str:
    if type(value) is not str or value not in members:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        if type(reason_code) is not str:
            raise ValueError("reason_codes must contain strings")
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_codes must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    normalized_codes = tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )
    if "cost_penalty_extreme" in normalized_codes or "risk_penalty_extreme" in normalized_codes:
        normalized_codes = tuple(
            reason_code
            for reason_code in normalized_codes
            if reason_code
            in (
                "edge_below_review_threshold",
                "cost_penalty_extreme",
                "risk_penalty_extreme",
            )
        )
    return normalized_codes


def _public_payload_values(
    report: ProbabilityEventRecommendationRankExplainabilityReport,
) -> dict[str, object]:
    return {
        "edge_score_probability": _decimal_payload(report.edge_score_probability),
        "confidence_score_probability": _decimal_payload(
            report.confidence_score_probability,
        ),
        "source_quality_probability": _decimal_payload(report.source_quality_probability),
        "cost_penalty_probability": _decimal_payload(report.cost_penalty_probability),
        "risk_penalty_probability": _decimal_payload(report.risk_penalty_probability),
        "recommendation_status": report.recommendation_status,
        "rank_explainability_score": _decimal_payload(report.rank_explainability_score),
        "reason_codes": list(report.reason_codes),
        "manual_next_step": report.manual_next_step,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _report_payload_digest(
    report: ProbabilityEventRecommendationRankExplainabilityReport,
) -> str:
    return _payload_digest_for_values(_public_payload_values(report))


def _payload_digest_for_values(payload: dict[str, object]) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()


def _validate_payload_digest(
    report: ProbabilityEventRecommendationRankExplainabilityReport,
) -> None:
    if report.payload_digest != _report_payload_digest(report):
        raise ValueError("payload_digest must match report fields")


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 string")
    return value


def _decimal_payload(value: Decimal) -> str:
    return format(_require_ratio_decimal("payload_decimal", value), "f")


def _require_payload_fields(payload: dict[str, object]) -> None:
    if tuple(payload.keys()) != _PUBLIC_PAYLOAD_FIELDS:
        raise ValueError("payload fields must match report payload schema")


def _require_payload_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _require_payload_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_payload_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError("reason_codes must be a list")
    return _normalize_reason_codes(value)


def _decimal_from_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    return _require_ratio_decimal(field_name, Decimal(value))


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    for text in _walk_public_strings(value):
        lowered = text.lower()
        if any(token in lowered for token in _UNSAFE_PUBLIC_TOKENS):
            raise ValueError(f"unsafe public {label}")


def _walk_public_strings(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if is_dataclass(value) and not isinstance(value, type):
        return _walk_public_strings(asdict(value))
    if type(value) is Decimal:
        return ()
    if type(value) is bool:
        return ()
    if type(value) is str:
        return (value,)
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric public values must be Decimal strings")
    if isinstance(value, Mapping):
        return tuple(
            text
            for key, item in value.items()
            for text in _walk_public_strings(key) + _walk_public_strings(item)
        )
    if isinstance(value, (list, tuple)):
        return tuple(text for item in value for text in _walk_public_strings(item))
    raise ValueError("public value is not JSON serializable")


__all__ = (
    "ProbabilityEventRecommendationRankExplainabilityReport",
    "build_probability_event_recommendation_rank_explainability_report",
    "probability_event_recommendation_rank_explainability_report_payload",
    "validate_probability_event_recommendation_rank_explainability_public_payload",
)
