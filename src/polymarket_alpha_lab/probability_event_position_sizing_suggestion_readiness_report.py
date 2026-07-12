"""Read-only probability event position sizing suggestion report."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "ProbabilityEventPositionSizingSuggestionReadinessInput",
    "ProbabilityEventPositionSizingSuggestionReadinessReport",
    "build_probability_event_position_sizing_suggestion_readiness_report",
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
READY_EDGE_FLOOR = Decimal("0.050000")
REVIEW_EDGE_FLOOR = Decimal("0.020000")
READY_CONFIDENCE_FLOOR = Decimal("0.700000")
REVIEW_CONFIDENCE_FLOOR = Decimal("0.500000")
READY_LIQUIDITY_FLOOR = Decimal("0.700000")
REVIEW_LIQUIDITY_FLOOR = Decimal("0.400000")
READY_CORRELATION_CEILING = Decimal("0.300000")
REVIEW_CORRELATION_CEILING = Decimal("0.500000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
REPORT_NOTICE = "manual_review_suggestion_only_not_submittable"
READY_NEXT_STEP = "manual_reviewer_verify_packet_before_any_submission"
REVIEW_NEXT_STEP = "manual_reviewer_resolve_reason_codes_before_sizing"
BLOCKED_NEXT_STEP = "manual_reviewer_do_not_size_until_blockers_clear"


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ProbabilityEventPositionSizingSuggestionReadinessInput(_FinalDataclass):
    net_edge_probability: Decimal
    confidence_probability: Decimal
    liquidity_score_probability: Decimal
    correlation_risk_probability: Decimal
    max_manual_size_probability: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventPositionSizingSuggestionReadinessInput,
            "readiness input",
        )
        for field_name in (
            "net_edge_probability",
            "confidence_probability",
            "liquidity_score_probability",
            "correlation_risk_probability",
            "max_manual_size_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("readiness input", self)


@dataclass(frozen=True)
class ProbabilityEventPositionSizingSuggestionReadinessReport(_FinalDataclass):
    sizing_status: str
    suggested_manual_size_probability: Decimal
    reason_codes: tuple[str, ...]
    manual_next_step: str
    net_edge_probability: Decimal
    confidence_probability: Decimal
    liquidity_score_probability: Decimal
    correlation_risk_probability: Decimal
    max_manual_size_probability: Decimal
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventPositionSizingSuggestionReadinessReport,
            "readiness report",
        )
        _require_status(self.sizing_status)
        object.__setattr__(
            self,
            "suggested_manual_size_probability",
            _normalize_probability(
                "suggested_manual_size_probability",
                self.suggested_manual_size_probability,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_public_string("manual_next_step", self.manual_next_step)
        for field_name in (
            "net_edge_probability",
            "confidence_probability",
            "liquidity_score_probability",
            "correlation_risk_probability",
            "max_manual_size_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_sha256("payload_digest", self.payload_digest)
        _require_hard_flags("readiness report", self)
        _validate_report(self)
        if self.payload_digest != _payload_digest(_public_payload_without_digest(self)):
            raise ValueError("payload_digest must match public payload")

    @property
    def public_payload(self) -> dict[str, object]:
        _require_hard_flags("readiness report", self)
        _validate_report(self)
        payload = _public_payload_without_digest(self)
        payload["payload_digest"] = self.payload_digest
        if self.payload_digest != _payload_digest(_payload_without_digest(payload)):
            raise ValueError("payload_digest must match public payload")
        return payload


def build_probability_event_position_sizing_suggestion_readiness_report(
    readiness_input: ProbabilityEventPositionSizingSuggestionReadinessInput,
) -> ProbabilityEventPositionSizingSuggestionReadinessReport:
    if type(readiness_input) is not ProbabilityEventPositionSizingSuggestionReadinessInput:
        raise ValueError(
            "readiness_input must be a "
            "ProbabilityEventPositionSizingSuggestionReadinessInput",
        )
    _require_hard_flags("readiness input", readiness_input)
    reason_codes = _reason_codes(readiness_input)
    sizing_status = _sizing_status(reason_codes)
    suggested_manual_size_probability = _suggested_manual_size(
        readiness_input,
        sizing_status,
    )
    manual_next_step = _manual_next_step(sizing_status)
    values: dict[str, object] = {
        "sizing_status": sizing_status,
        "suggested_manual_size_probability": suggested_manual_size_probability,
        "reason_codes": reason_codes,
        "manual_next_step": manual_next_step,
        "net_edge_probability": readiness_input.net_edge_probability,
        "confidence_probability": readiness_input.confidence_probability,
        "liquidity_score_probability": readiness_input.liquidity_score_probability,
        "correlation_risk_probability": readiness_input.correlation_risk_probability,
        "max_manual_size_probability": readiness_input.max_manual_size_probability,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    digest = _payload_digest(_public_payload_from_values(values))
    return ProbabilityEventPositionSizingSuggestionReadinessReport(
        **values,
        payload_digest=digest,
    )


def _reason_codes(
    readiness_input: ProbabilityEventPositionSizingSuggestionReadinessInput,
) -> tuple[str, ...]:
    blocked_codes: list[str] = []
    if readiness_input.net_edge_probability < REVIEW_EDGE_FLOOR:
        blocked_codes.append("net_edge_probability_below_review_floor")
    if readiness_input.confidence_probability < REVIEW_CONFIDENCE_FLOOR:
        blocked_codes.append("confidence_probability_below_review_floor")
    if readiness_input.liquidity_score_probability < REVIEW_LIQUIDITY_FLOOR:
        blocked_codes.append("liquidity_score_probability_below_review_floor")
    if readiness_input.correlation_risk_probability > REVIEW_CORRELATION_CEILING:
        blocked_codes.append("correlation_risk_probability_above_review_ceiling")
    if readiness_input.max_manual_size_probability == ZERO:
        blocked_codes.append("max_manual_size_probability_zero")
    if blocked_codes:
        return tuple(blocked_codes)

    review_codes: list[str] = []
    if readiness_input.net_edge_probability < READY_EDGE_FLOOR:
        review_codes.append("net_edge_probability_below_ready_floor")
    if readiness_input.confidence_probability < READY_CONFIDENCE_FLOOR:
        review_codes.append("confidence_probability_below_ready_floor")
    if readiness_input.liquidity_score_probability < READY_LIQUIDITY_FLOOR:
        review_codes.append("liquidity_score_probability_below_ready_floor")
    if readiness_input.correlation_risk_probability > READY_CORRELATION_CEILING:
        review_codes.append("correlation_risk_probability_above_ready_ceiling")
    if review_codes:
        return tuple(review_codes)
    return ("manual_sizing_suggestion_ready_for_human_review",)


def _sizing_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("manual_sizing_suggestion_ready_for_human_review",):
        return "ready"
    if any("review_floor" in reason_code or "review_ceiling" in reason_code for reason_code in reason_codes):
        return "blocked"
    if "max_manual_size_probability_zero" in reason_codes:
        return "blocked"
    return "review"


def _suggested_manual_size(
    readiness_input: ProbabilityEventPositionSizingSuggestionReadinessInput,
    sizing_status: str,
) -> Decimal:
    if sizing_status == "blocked":
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        raw_size = (
            readiness_input.net_edge_probability
            * readiness_input.confidence_probability
            * readiness_input.liquidity_score_probability
            * (ONE - readiness_input.correlation_risk_probability)
        )
    if raw_size > readiness_input.max_manual_size_probability:
        raw_size = readiness_input.max_manual_size_probability
    return _normalize_probability("suggested_manual_size_probability", raw_size)


def _manual_next_step(sizing_status: str) -> str:
    if sizing_status == "ready":
        return READY_NEXT_STEP
    if sizing_status == "review":
        return REVIEW_NEXT_STEP
    return BLOCKED_NEXT_STEP


def _public_payload_without_digest(
    report: ProbabilityEventPositionSizingSuggestionReadinessReport,
) -> dict[str, object]:
    return {
        "sizing_status": report.sizing_status,
        "suggested_manual_size_probability": _decimal_text(
            report.suggested_manual_size_probability,
        ),
        "reason_codes": list(report.reason_codes),
        "manual_next_step": report.manual_next_step,
        "net_edge_probability": _decimal_text(report.net_edge_probability),
        "confidence_probability": _decimal_text(report.confidence_probability),
        "liquidity_score_probability": _decimal_text(report.liquidity_score_probability),
        "correlation_risk_probability": _decimal_text(report.correlation_risk_probability),
        "max_manual_size_probability": _decimal_text(report.max_manual_size_probability),
        "report_notice": REPORT_NOTICE,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _public_payload_from_values(values: dict[str, object]) -> dict[str, object]:
    return {
        "sizing_status": values["sizing_status"],
        "suggested_manual_size_probability": _decimal_text(
            values["suggested_manual_size_probability"],
        ),
        "reason_codes": list(_reason_codes_tuple(values["reason_codes"])),
        "manual_next_step": values["manual_next_step"],
        "net_edge_probability": _decimal_text(values["net_edge_probability"]),
        "confidence_probability": _decimal_text(values["confidence_probability"]),
        "liquidity_score_probability": _decimal_text(values["liquidity_score_probability"]),
        "correlation_risk_probability": _decimal_text(values["correlation_risk_probability"]),
        "max_manual_size_probability": _decimal_text(values["max_manual_size_probability"]),
        "report_notice": REPORT_NOTICE,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _payload_without_digest(payload: dict[str, object]) -> dict[str, object]:
    values = dict(payload)
    values.pop("payload_digest", None)
    return values


def _payload_digest(payload: dict[str, object]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _validate_report(
    report: ProbabilityEventPositionSizingSuggestionReadinessReport,
) -> None:
    expected_status = _sizing_status(report.reason_codes)
    if report.sizing_status != expected_status:
        raise ValueError("sizing_status must match reason_codes")
    if report.manual_next_step != _manual_next_step(report.sizing_status):
        raise ValueError("manual_next_step must match sizing_status")
    if report.sizing_status == "blocked" and report.suggested_manual_size_probability != ZERO:
        raise ValueError("blocked reports must have zero suggested_manual_size_probability")
    if report.suggested_manual_size_probability > report.max_manual_size_probability:
        raise ValueError(
            "suggested_manual_size_probability must not exceed max_manual_size_probability",
        )


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _normalize_probability(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(QUANTUM)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not value:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    for reason_code in value:
        _require_public_string("reason_codes", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(normalized)


def _reason_codes_tuple(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    return value


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a stripped non-empty string")


def _require_status(value: object) -> None:
    if value not in ("ready", "review", "blocked"):
        raise ValueError("sizing_status must be ready, review, or blocked")


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} must keep {field_name}=True")


def _decimal_text(value: object) -> str:
    if type(value) is not Decimal:
        raise ValueError("payload decimal values must be Decimal")
    with localcontext(DECIMAL_CONTEXT):
        return format(value.quantize(QUANTUM), "f")
