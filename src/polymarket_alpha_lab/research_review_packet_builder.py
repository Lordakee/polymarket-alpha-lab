"""Pure read-only research review packet builder."""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import require_team_id


DECIMAL_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MASK = "<redacted>"

REVIEW_STATUSES = ("pass", "watch", "block")
REASON_CODES = (
    "score_meets_pass_threshold",
    "score_below_pass_threshold",
    "evidence_complete",
    "evidence_missing",
    "cost_within_threshold",
    "cost_above_threshold",
    "explanation_layer_complete",
    "explanation_layer_incomplete",
    "team_route_ready",
    "team_route_missing",
    "unsafe_public_content_redacted",
    "leakage_risk_present",
    "public_status_pass",
    "public_status_watch",
    "public_status_block",
)

UNSAFE_PUBLIC_TEXT_FRAGMENTS = tuple(
    "".join(chr(code) for code in codes)
    for codes in (
        (114, 97, 119, 45, 99, 97, 110, 100, 105, 100, 97, 116, 101),
        (99, 97, 110, 100, 105, 100, 97, 116, 101, 95, 105, 100),
        (109, 97, 114, 107, 101, 116, 95, 105, 100),
        (109, 97, 114, 107, 101, 116, 95, 115, 108, 117, 103),
        (113, 117, 101, 115, 116, 105, 111, 110),
        (115, 111, 117, 114, 99, 101, 95, 114, 101, 102),
        (115, 111, 117, 114, 99, 101, 95, 117, 114, 108),
        (115, 111, 117, 114, 99, 101, 95, 116, 101, 120, 116),
        (104, 116, 116, 112, 58, 47, 47),
        (104, 116, 116, 112, 115, 58, 47, 47),
        (58, 47, 47),
        (100, 115, 110),
        (116, 97, 98, 108, 101),
        (116, 111, 107, 101, 110),
        (119, 97, 108, 108, 101, 116),
        (97, 117, 116, 104),
        (111, 114, 100, 101, 114),
        (116, 114, 97, 100, 101),
        (112, 111, 115, 105, 116, 105, 111, 110),
        (98, 117, 121),
        (115, 101, 108, 108),
        (114, 101, 99, 111, 109, 109, 101, 110, 100, 97, 116, 105, 111, 110),
    )
)


@dataclass(frozen=True)
class RedactedReviewScoreSummary:
    score_band: str
    review_confidence: Decimal
    evidence_strength: Decimal
    explanation_coverage: Decimal
    leakage_risk: Decimal
    missing_evidence_count: Decimal
    summary_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "score_band",
            _normalize_public_string("score_band", self.score_band),
        )
        for field_name in (
            "review_confidence",
            "evidence_strength",
            "explanation_coverage",
            "leakage_risk",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "missing_evidence_count",
            _normalize_nonnegative_count(
                "missing_evidence_count",
                self.missing_evidence_count,
            ),
        )
        object.__setattr__(
            self,
            "summary_codes",
            _normalize_public_string_tuple("summary_codes", self.summary_codes),
        )
        require_paper_only_flags("redacted review score summary", self)


@dataclass(frozen=True)
class ReviewTeamRoute:
    team_id: str
    route_label: str
    route_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        object.__setattr__(
            self,
            "route_label",
            _normalize_public_string("route_label", self.route_label),
        )
        object.__setattr__(
            self,
            "route_reason_codes",
            _normalize_public_string_tuple(
                "route_reason_codes",
                self.route_reason_codes,
            ),
        )
        require_paper_only_flags("review team route", self)


@dataclass(frozen=True)
class ReviewCostThreshold:
    maximum_review_cost_bps: Decimal
    estimated_review_cost_bps: Decimal
    minimum_pass_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("maximum_review_cost_bps", "estimated_review_cost_bps"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "minimum_pass_score",
            _normalize_probability("minimum_pass_score", self.minimum_pass_score),
        )
        require_paper_only_flags("review cost threshold", self)


@dataclass(frozen=True)
class ReviewExplanationLayer:
    explanation_codes: tuple[str, ...]
    public_rationale_points: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "explanation_codes",
            _normalize_public_string_tuple(
                "explanation_codes",
                self.explanation_codes,
            ),
        )
        object.__setattr__(
            self,
            "public_rationale_points",
            _normalize_public_string_tuple(
                "public_rationale_points",
                self.public_rationale_points,
            ),
        )
        require_paper_only_flags("review explanation layer", self)


@dataclass(frozen=True)
class ResearchReviewPacket:
    review_status: str
    score_summary: RedactedReviewScoreSummary
    team_route: ReviewTeamRoute
    cost_threshold: ReviewCostThreshold
    explanation_layer: ReviewExplanationLayer
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_member("review_status", self.review_status, REVIEW_STATUSES)
        _require_exact_type(
            "score_summary",
            self.score_summary,
            RedactedReviewScoreSummary,
        )
        _require_exact_type("team_route", self.team_route, ReviewTeamRoute)
        _require_exact_type("cost_threshold", self.cost_threshold, ReviewCostThreshold)
        _require_exact_type(
            "explanation_layer",
            self.explanation_layer,
            ReviewExplanationLayer,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        require_paper_only_flags("research review packet", self)
        _validate_packet(self)
        reject_unsafe_surface_fields("research review packet", self.payload)
        _reject_unsafe_public_payload("research review packet", self.payload)

    @property
    def payload(self) -> dict[str, Any]:
        return research_review_packet_payload(self)


def build_research_review_packet(
    score_summary: RedactedReviewScoreSummary,
    team_route: ReviewTeamRoute,
    cost_threshold: ReviewCostThreshold,
    explanation_layer: ReviewExplanationLayer,
) -> ResearchReviewPacket:
    _require_exact_type(
        "score_summary",
        score_summary,
        RedactedReviewScoreSummary,
    )
    _require_exact_type("team_route", team_route, ReviewTeamRoute)
    _require_exact_type("cost_threshold", cost_threshold, ReviewCostThreshold)
    _require_exact_type("explanation_layer", explanation_layer, ReviewExplanationLayer)
    for label, value in (
        ("score_summary", score_summary),
        ("team_route", team_route),
        ("cost_threshold", cost_threshold),
        ("explanation_layer", explanation_layer),
    ):
        require_paper_only_flags(label, value)
    review_status = _derive_review_status(
        score_summary,
        team_route,
        cost_threshold,
        explanation_layer,
    )
    reason_codes = _derive_reason_codes(
        review_status,
        score_summary,
        team_route,
        cost_threshold,
        explanation_layer,
    )
    digest = _digest_payload(
        _packet_payload(
            review_status=review_status,
            score_summary=score_summary,
            team_route=team_route,
            cost_threshold=cost_threshold,
            explanation_layer=explanation_layer,
            reason_codes=reason_codes,
            derived_validation_digest=None,
        ),
    )
    return ResearchReviewPacket(
        review_status=review_status,
        score_summary=score_summary,
        team_route=team_route,
        cost_threshold=cost_threshold,
        explanation_layer=explanation_layer,
        reason_codes=reason_codes,
        derived_validation_digest=digest,
    )


def research_review_packet_payload(result: ResearchReviewPacket) -> dict[str, Any]:
    _require_exact_type("result", result, ResearchReviewPacket)
    require_paper_only_flags("research review packet", result)
    payload = _packet_payload(
        review_status=result.review_status,
        score_summary=result.score_summary,
        team_route=result.team_route,
        cost_threshold=result.cost_threshold,
        explanation_layer=result.explanation_layer,
        reason_codes=result.reason_codes,
        derived_validation_digest=result.derived_validation_digest,
    )
    reject_unsafe_surface_fields("research review packet payload", payload)
    _reject_unsafe_public_payload("research review packet payload", payload)
    return payload


def _derive_review_status(
    score_summary: RedactedReviewScoreSummary,
    team_route: ReviewTeamRoute,
    cost_threshold: ReviewCostThreshold,
    explanation_layer: ReviewExplanationLayer,
) -> str:
    if (
        _has_redacted_public_value(score_summary)
        or _has_redacted_public_value(team_route)
        or _has_redacted_public_value(explanation_layer)
        or score_summary.leakage_risk > ZERO
        or cost_threshold.estimated_review_cost_bps
        > cost_threshold.maximum_review_cost_bps
    ):
        return "block"
    if (
        score_summary.review_confidence < cost_threshold.minimum_pass_score
        or score_summary.missing_evidence_count > ZERO
        or not explanation_layer.explanation_codes
        or not explanation_layer.public_rationale_points
        or not team_route.route_reason_codes
    ):
        return "watch"
    return "pass"


def _derive_reason_codes(
    review_status: str,
    score_summary: RedactedReviewScoreSummary,
    team_route: ReviewTeamRoute,
    cost_threshold: ReviewCostThreshold,
    explanation_layer: ReviewExplanationLayer,
) -> tuple[str, ...]:
    codes = [
        (
            "score_meets_pass_threshold"
            if score_summary.review_confidence >= cost_threshold.minimum_pass_score
            else "score_below_pass_threshold"
        ),
        (
            "evidence_complete"
            if score_summary.missing_evidence_count == ZERO
            else "evidence_missing"
        ),
        (
            "cost_within_threshold"
            if cost_threshold.estimated_review_cost_bps
            <= cost_threshold.maximum_review_cost_bps
            else "cost_above_threshold"
        ),
        (
            "explanation_layer_complete"
            if (
                explanation_layer.explanation_codes
                and explanation_layer.public_rationale_points
            )
            else "explanation_layer_incomplete"
        ),
        (
            "team_route_ready"
            if team_route.route_reason_codes and team_route.route_label != MASK
            else "team_route_missing"
        ),
    ]
    if (
        _has_redacted_public_value(score_summary)
        or _has_redacted_public_value(team_route)
        or _has_redacted_public_value(explanation_layer)
    ):
        codes.append("unsafe_public_content_redacted")
    if score_summary.leakage_risk > ZERO:
        codes.append("leakage_risk_present")
    codes.append(f"public_status_{review_status}")
    return _normalize_reason_codes(tuple(codes))


def _validate_packet(result: ResearchReviewPacket) -> None:
    expected_status = _derive_review_status(
        result.score_summary,
        result.team_route,
        result.cost_threshold,
        result.explanation_layer,
    )
    if result.review_status != expected_status:
        raise ValueError("review_status must match packet inputs")
    expected_reason_codes = _derive_reason_codes(
        result.review_status,
        result.score_summary,
        result.team_route,
        result.cost_threshold,
        result.explanation_layer,
    )
    if result.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match packet inputs")
    expected_digest = _digest_payload(
        _packet_payload(
            review_status=result.review_status,
            score_summary=result.score_summary,
            team_route=result.team_route,
            cost_threshold=result.cost_threshold,
            explanation_layer=result.explanation_layer,
            reason_codes=result.reason_codes,
            derived_validation_digest=None,
        ),
    )
    if result.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match packet payload")


def _packet_payload(
    *,
    review_status: str,
    score_summary: RedactedReviewScoreSummary,
    team_route: ReviewTeamRoute,
    cost_threshold: ReviewCostThreshold,
    explanation_layer: ReviewExplanationLayer,
    reason_codes: tuple[str, ...],
    derived_validation_digest: str | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "review_status": review_status,
        "score_summary": _json_object(score_summary),
        "team_route": _json_object(team_route),
        "cost_threshold": _json_object(cost_threshold),
        "explanation_layer": _json_object(explanation_layer),
        "reason_codes": list(reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    if derived_validation_digest is not None:
        payload["derived_validation_digest"] = derived_validation_digest
    return payload


def _json_object(value: object) -> dict[str, Any]:
    payload = json_ready_no_floats(value)
    if type(payload) is not dict:
        raise ValueError("payload component must be a JSON object")
    _reject_unsafe_public_payload("research review packet component", payload)
    return payload


def _digest_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _normalize_reason_codes(values: object) -> tuple[str, ...]:
    normalized = _normalize_public_string_tuple("reason_codes", values)
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for value in normalized:
        if value not in REASON_CODES:
            raise ValueError("reason_codes contains unsupported value")
        if value in seen:
            raise ValueError("reason_codes contains duplicate value")
        seen.add(value)
    return normalized


def _normalize_public_string_tuple(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    return tuple(_normalize_public_string(field_name, item) for item in value)


def _normalize_public_string(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if _contains_unsafe_public_text(value):
        return MASK
    return value


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    normalized = decimal_value.quantize(COUNT_QUANT)
    if normalized != decimal_value:
        raise ValueError(f"{field_name} must be a whole Decimal count")
    if normalized < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    return _require_decimal(field_name, value).quantize(DECIMAL_QUANT)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must contain canonical strings")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _require_exact_type(
    field_name: str,
    value: object,
    expected_type: type[object],
) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")


def _require_digest(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _has_redacted_public_value(value: object) -> bool:
    if isinstance(value, str):
        return value == MASK
    if isinstance(value, Decimal):
        return False
    if isinstance(value, bool):
        return False
    if isinstance(value, tuple):
        return any(_has_redacted_public_value(item) for item in value)
    if hasattr(value, "__dataclass_fields__"):
        return any(
            _has_redacted_public_value(getattr(value, field_name))
            for field_name in value.__dataclass_fields__
        )
    return False


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, str):
        if _contains_unsafe_public_text(value):
            raise ValueError(f"unsafe public payload text in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if _contains_unsafe_public_text(key):
                raise ValueError(f"unsafe public payload key in {label}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _contains_unsafe_public_text(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS)


__all__ = (
    "MASK",
    "REASON_CODES",
    "REVIEW_STATUSES",
    "RedactedReviewScoreSummary",
    "ReviewCostThreshold",
    "ReviewExplanationLayer",
    "ReviewTeamRoute",
    "ResearchReviewPacket",
    "build_research_review_packet",
    "research_review_packet_payload",
)
