"""Review freshness escalation report for probability event markets."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Mapping


__all__ = (
    "PROBABILITY_EVENT_REVIEW_FRESHNESS_ESCALATION_REPORT_VERSION",
    "ProbabilityEventReviewFreshnessEscalationInput",
    "ProbabilityEventReviewFreshnessEscalationReport",
    "build_probability_event_review_freshness_escalation_report",
    "probability_event_review_freshness_escalation_report_payload",
)


PROBABILITY_EVENT_REVIEW_FRESHNESS_ESCALATION_REPORT_VERSION = (
    "probability-event-review-freshness-escalation-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
OPERATOR_REVIEW_STALE_AFTER_HOURS = Decimal("12.000000")
OPERATOR_REVIEW_EXPIRED_AFTER_HOURS = Decimal("24.000000")
SOURCE_REFRESH_STALE_AFTER_HOURS = Decimal("6.000000")
SOURCE_REFRESH_EXPIRED_AFTER_HOURS = Decimal("12.000000")
PRICE_MOVE_REVIEW_THRESHOLD = Decimal("0.100000")
MARKET_CLOSE_IMMINENT_HOURS = Decimal("6.000000")

ESCALATION_STATUSES = (
    "current",
    "manual_review",
    "urgent_manual_review",
)
REASON_CODES = (
    "operator_review_stale",
    "operator_review_expired",
    "source_refresh_stale",
    "source_refresh_expired",
    "price_move_requires_review",
    "market_close_imminent",
    "blocking_reasons_present",
)
URGENT_REASON_CODES = (
    "operator_review_expired",
    "source_refresh_expired",
    "price_move_requires_review",
    "market_close_imminent",
)
MANUAL_NEXT_STEPS = (
    "continue_standard_monitoring",
    "schedule_operator_review",
    "refresh_sources_before_review",
    "refresh_sources_then_operator_review",
    "resolve_blocking_reasons_manually",
    "escalate_to_operator_before_any_action",
)
PAYLOAD_KEYS = (
    "config_version",
    "last_operator_review_age_hours",
    "source_refresh_age_hours",
    "price_move_since_review_probability",
    "market_close_hours",
    "blocking_reason_count",
    "escalation_status",
    "reason_codes",
    "manual_next_step",
    "paper_only",
    "report_only",
    "readonly",
)


class ProbabilityEventReviewFreshnessEscalationPublicPayload(dict[str, object]):
    """Immutable public payload for the review freshness report."""

    def __readonly(self, *args: object, **kwargs: object) -> None:
        raise TypeError("public_payload is immutable")

    __setitem__ = __readonly
    __delitem__ = __readonly
    clear = __readonly
    pop = __readonly
    popitem = __readonly
    setdefault = __readonly
    update = __readonly


@dataclass(frozen=True)
class ProbabilityEventReviewFreshnessEscalationInput:
    last_operator_review_age_hours: Decimal
    source_refresh_age_hours: Decimal
    price_move_since_review_probability: Decimal
    market_close_hours: Decimal
    blocking_reason_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventReviewFreshnessEscalationInput:
            raise TypeError(
                "ProbabilityEventReviewFreshnessEscalationInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventReviewFreshnessEscalationInput:
            raise ValueError(
                "input must be exactly ProbabilityEventReviewFreshnessEscalationInput",
            )
        object.__setattr__(
            self,
            "last_operator_review_age_hours",
            _require_nonnegative_decimal(
                "last_operator_review_age_hours",
                self.last_operator_review_age_hours,
            ),
        )
        object.__setattr__(
            self,
            "source_refresh_age_hours",
            _require_nonnegative_decimal(
                "source_refresh_age_hours",
                self.source_refresh_age_hours,
            ),
        )
        object.__setattr__(
            self,
            "price_move_since_review_probability",
            _require_probability_decimal(
                "price_move_since_review_probability",
                self.price_move_since_review_probability,
            ),
        )
        object.__setattr__(
            self,
            "market_close_hours",
            _require_nonnegative_decimal("market_close_hours", self.market_close_hours),
        )
        object.__setattr__(
            self,
            "blocking_reason_count",
            _require_count_decimal("blocking_reason_count", self.blocking_reason_count),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ProbabilityEventReviewFreshnessEscalationReport:
    config_version: str
    last_operator_review_age_hours: Decimal
    source_refresh_age_hours: Decimal
    price_move_since_review_probability: Decimal
    market_close_hours: Decimal
    blocking_reason_count: Decimal
    escalation_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventReviewFreshnessEscalationReport:
            raise TypeError(
                "ProbabilityEventReviewFreshnessEscalationReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventReviewFreshnessEscalationReport:
            raise ValueError(
                "report must be exactly ProbabilityEventReviewFreshnessEscalationReport",
            )
        _require_config_version(self.config_version)
        object.__setattr__(
            self,
            "last_operator_review_age_hours",
            _require_nonnegative_decimal(
                "last_operator_review_age_hours",
                self.last_operator_review_age_hours,
            ),
        )
        object.__setattr__(
            self,
            "source_refresh_age_hours",
            _require_nonnegative_decimal(
                "source_refresh_age_hours",
                self.source_refresh_age_hours,
            ),
        )
        object.__setattr__(
            self,
            "price_move_since_review_probability",
            _require_probability_decimal(
                "price_move_since_review_probability",
                self.price_move_since_review_probability,
            ),
        )
        object.__setattr__(
            self,
            "market_close_hours",
            _require_nonnegative_decimal("market_close_hours", self.market_close_hours),
        )
        object.__setattr__(
            self,
            "blocking_reason_count",
            _require_count_decimal("blocking_reason_count", self.blocking_reason_count),
        )
        _require_escalation_status(self.escalation_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_manual_next_step(self.manual_next_step)
        _require_hard_flags(self)
        _validate_report(self)

    @property
    def public_payload(self) -> ProbabilityEventReviewFreshnessEscalationPublicPayload:
        payload = ProbabilityEventReviewFreshnessEscalationPublicPayload(
            _payload_items(self),
        )
        _validate_public_payload(payload)
        return payload


def build_probability_event_review_freshness_escalation_report(
    inputs: ProbabilityEventReviewFreshnessEscalationInput,
) -> ProbabilityEventReviewFreshnessEscalationReport:
    """Build a deterministic review escalation summary."""

    if type(inputs) is not ProbabilityEventReviewFreshnessEscalationInput:
        raise ValueError(
            "inputs must be a ProbabilityEventReviewFreshnessEscalationInput",
        )
    _require_hard_flags(inputs)
    reason_codes = _reason_codes(inputs)
    escalation_status = _escalation_status(reason_codes)
    manual_next_step = _manual_next_step(reason_codes, escalation_status)
    return ProbabilityEventReviewFreshnessEscalationReport(
        config_version=PROBABILITY_EVENT_REVIEW_FRESHNESS_ESCALATION_REPORT_VERSION,
        last_operator_review_age_hours=inputs.last_operator_review_age_hours,
        source_refresh_age_hours=inputs.source_refresh_age_hours,
        price_move_since_review_probability=inputs.price_move_since_review_probability,
        market_close_hours=inputs.market_close_hours,
        blocking_reason_count=inputs.blocking_reason_count,
        escalation_status=escalation_status,
        reason_codes=reason_codes,
        manual_next_step=manual_next_step,
    )


def probability_event_review_freshness_escalation_report_payload(
    report: ProbabilityEventReviewFreshnessEscalationReport,
) -> ProbabilityEventReviewFreshnessEscalationPublicPayload:
    if type(report) is not ProbabilityEventReviewFreshnessEscalationReport:
        raise ValueError(
            "report must be a ProbabilityEventReviewFreshnessEscalationReport",
        )
    _require_hard_flags(report)
    _validate_report(report)
    return report.public_payload


def _reason_codes(
    value: ProbabilityEventReviewFreshnessEscalationInput
    | ProbabilityEventReviewFreshnessEscalationReport,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if value.last_operator_review_age_hours >= OPERATOR_REVIEW_EXPIRED_AFTER_HOURS:
        reasons.append("operator_review_expired")
    elif value.last_operator_review_age_hours >= OPERATOR_REVIEW_STALE_AFTER_HOURS:
        reasons.append("operator_review_stale")
    if value.source_refresh_age_hours >= SOURCE_REFRESH_EXPIRED_AFTER_HOURS:
        reasons.append("source_refresh_expired")
    elif value.source_refresh_age_hours >= SOURCE_REFRESH_STALE_AFTER_HOURS:
        reasons.append("source_refresh_stale")
    if value.price_move_since_review_probability >= PRICE_MOVE_REVIEW_THRESHOLD:
        reasons.append("price_move_requires_review")
    if value.market_close_hours <= MARKET_CLOSE_IMMINENT_HOURS:
        reasons.append("market_close_imminent")
    if value.blocking_reason_count > ZERO:
        reasons.append("blocking_reasons_present")
    return tuple(reasons)


def _escalation_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in URGENT_REASON_CODES for reason_code in reason_codes):
        return "urgent_manual_review"
    if reason_codes:
        return "manual_review"
    return "current"


def _manual_next_step(reason_codes: tuple[str, ...], escalation_status: str) -> str:
    if escalation_status == "urgent_manual_review":
        return "escalate_to_operator_before_any_action"
    if "blocking_reasons_present" in reason_codes:
        return "resolve_blocking_reasons_manually"
    if "source_refresh_stale" in reason_codes and "operator_review_stale" in reason_codes:
        return "refresh_sources_then_operator_review"
    if "source_refresh_stale" in reason_codes:
        return "refresh_sources_before_review"
    if "operator_review_stale" in reason_codes:
        return "schedule_operator_review"
    return "continue_standard_monitoring"


def _validate_report(report: ProbabilityEventReviewFreshnessEscalationReport) -> None:
    expected_reason_codes = _reason_codes(report)
    expected_status = _escalation_status(expected_reason_codes)
    expected_step = _manual_next_step(expected_reason_codes, expected_status)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match review freshness inputs")
    if report.escalation_status != expected_status:
        raise ValueError("escalation_status must match reason_codes")
    if report.manual_next_step != expected_step:
        raise ValueError("manual_next_step must match review state")


def _validate_public_payload(
    payload: Mapping[str, object],
) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    if tuple(payload.keys()) != PAYLOAD_KEYS:
        raise ValueError("payload must match the review freshness schema")
    _require_config_version(payload["config_version"])
    for field_name in (
        "last_operator_review_age_hours",
        "source_refresh_age_hours",
        "price_move_since_review_probability",
        "market_close_hours",
        "blocking_reason_count",
    ):
        if type(payload[field_name]) is not str:
            raise ValueError(f"{field_name} must be serialized as a string")
    _require_nonnegative_decimal(
        "last_operator_review_age_hours",
        Decimal(payload["last_operator_review_age_hours"]),
    )
    _require_nonnegative_decimal(
        "source_refresh_age_hours",
        Decimal(payload["source_refresh_age_hours"]),
    )
    _require_probability_decimal(
        "price_move_since_review_probability",
        Decimal(payload["price_move_since_review_probability"]),
    )
    _require_nonnegative_decimal(
        "market_close_hours",
        Decimal(payload["market_close_hours"]),
    )
    _require_count_decimal(
        "blocking_reason_count",
        Decimal(payload["blocking_reason_count"]),
    )
    _require_escalation_status(payload["escalation_status"])
    _normalize_reason_codes(payload["reason_codes"])
    _require_manual_next_step(payload["manual_next_step"])
    for field_name in ("paper_only", "report_only", "readonly"):
        _require_bool(field_name, payload[field_name])
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    return payload


def _payload_items(
    report: ProbabilityEventReviewFreshnessEscalationReport,
) -> dict[str, object]:
    return {
        "config_version": report.config_version,
        "last_operator_review_age_hours": _decimal_text(
            report.last_operator_review_age_hours,
        ),
        "source_refresh_age_hours": _decimal_text(report.source_refresh_age_hours),
        "price_move_since_review_probability": _decimal_text(
            report.price_move_since_review_probability,
        ),
        "market_close_hours": _decimal_text(report.market_close_hours),
        "blocking_reason_count": _decimal_text(report.blocking_reason_count),
        "escalation_status": report.escalation_status,
        "reason_codes": report.reason_codes,
        "manual_next_step": report.manual_next_step,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    seen: set[str] = set()
    for reason_code in value:
        if type(reason_code) is not str or reason_code not in REASON_CODES:
            raise ValueError("reason_codes must be supported")
        if reason_code in seen:
            raise ValueError("reason_codes must not repeat values")
        seen.add(reason_code)
    return value


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = getattr(value, field_name)
        if flag is not True:
            raise ValueError(f"{field_name} must be True")


def _require_config_version(value: object) -> None:
    if value != PROBABILITY_EVENT_REVIEW_FRESHNESS_ESCALATION_REPORT_VERSION:
        raise ValueError("config_version must be the supported report version")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be exactly bool")


def _require_escalation_status(value: object) -> None:
    if type(value) is not str or value not in ESCALATION_STATUSES:
        raise ValueError("escalation_status must be supported")


def _require_manual_next_step(value: object) -> None:
    if type(value) is not str or value not in MANUAL_NEXT_STEPS:
        raise ValueError("manual_next_step must be supported")


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _decimal_text(value: object) -> str:
    if type(value) is not Decimal:
        raise ValueError("public numeric value must be Decimal")
    return format(value.quantize(QUANTUM, rounding=ROUND_HALF_UP), "f")
